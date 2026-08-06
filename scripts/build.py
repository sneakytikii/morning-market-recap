#!/usr/bin/env python3
"""Render data/*.json into dashboard.html, then into the two distributable builds.

DESIGN NOTE — why marker injection rather than a real template engine:

The page is 80KB of hand-tuned markup carrying a lot of hard-won work: WCAG AA colour
pairs verified by computation, an ARIA tablist, bilingual EN/KO duplicate-DOM parity, a
28x28 pixel sprite, and a layout that was rebuilt once already because it was too dense.
Regenerating all of that from a template every morning would put every one of those
properties at risk daily, for no benefit — the *structure* never changes, only the numbers
and the news.

So the HTML stays the source of truth for structure, and carries markers around the parts
that change:

    <!--F:spx.price-->6,388.64<!--/F-->                    a single value
    <!--R:trump-->  ...{{quote}}...  <!--/R-->             a repeating block

The build replaces marker contents from JSON and leaves everything else byte-identical.
If the data is missing or malformed the build refuses to write, and yesterday's page —
which is known-good — stays up. A stale correct page beats a fresh broken one.
"""
import re
import sys
import json
import html
import shutil
import pathlib
import datetime
import zoneinfo

# The reader's clock is US Pacific (Daniel's dad reads from PST). Every "what day is
# it" decision — masthead date, Today label, freshness age — uses this zone, never the
# build machine's local clock, so the page stays right even if the Mac travels.
PACIFIC = zoneinfo.ZoneInfo("America/Los_Angeles")


def pacific_today() -> datetime.date:
    return datetime.datetime.now(PACIFIC).date()

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Template and output are SEPARATE FILES, and that separation is load-bearing.
#
# The first version of this script rendered dashboard.html in place. That works exactly
# once: rendering replaces the contents of a <!--R:…--> block with the rendered rows, so
# the next build treats six rendered entries as the template and emits thirty-six.
# Keeping the source read-only makes the build idempotent — run it a hundred times and
# the output is byte-identical.
#
# EDIT dashboard.template.html. dashboard.html is generated; edits to it are overwritten.
TEMPLATE = ROOT / "dashboard.template.html"
OUTPUT = ROOT / "dashboard.html"
DATA = ROOT / "data"
BACKUPS = ROOT / "backups"

FIELD_RE = re.compile(r"<!--F:([a-zA-Z0-9_.\-]+)(\|raw|\|js)?-->(.*?)<!--/F-->", re.S)
REPEAT_RE = re.compile(r"<!--R:([a-zA-Z0-9_.\-]+)-->(.*?)<!--/R-->", re.S)
PLACEHOLDER_RE = re.compile(r"\{\{([a-zA-Z0-9_.\-]+)(\|raw)?\}\}")


class BuildError(Exception):
    pass


def dotted(data, path):
    """Look up 'spx.price' in nested dicts. Missing keys raise rather than blank the page."""
    cur = data
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise BuildError(f"data key not found: {path!r}")
    return cur


IF_RE = re.compile(r"\{\{#if ([a-zA-Z0-9_.\-]+)\}\}(.*?)\{\{/if\}\}", re.S)


def render_placeholders(block: str, item: dict, name: str) -> str:
    """Substitute {{field}} inside one repeat item. Escaped by default; {{field|raw}}
    passes markup through, which is needed because a lot of the copy carries inline <b>.

    {{#if field}}…{{/if}} drops its contents when the field is absent, empty, or false.
    Entries legitimately differ — a policy action has no quote, a disclosed trade has no
    measured price reaction — and the alternative is empty elements the CSS has to hide."""
    def cond(m):
        key, body = m.group(1), m.group(2)
        val = item.get(key)
        keep = bool(val) and val != "" and val != []
        return body if keep else ""

    block = IF_RE.sub(cond, block)

    def sub(m):
        key, raw = m.group(1), m.group(2)
        if key not in item:
            raise BuildError(f"repeat {name!r}: item missing field {key!r}")
        val = item[key]
        if val is None:
            return ""
        val = str(val)
        return val if raw else html.escape(val, quote=False)

    return PLACEHOLDER_RE.sub(sub, block)


# Which of the five positions a chip-policy item actually reaches. NVDA is held outright,
# sits inside SPX and QQQ, and is levered 3x inside SOXL — so one export rule touches four
# of five at once. That fact is the whole reason this section is on the page.
POS_LABEL = {"spx": "SPX", "qqq": "QQQ", "nvda": "NVDA", "soxl": "SOXL", "cost": "COST"}


BOARD_ORDER = ("spx", "qqq", "nvda", "soxl", "cost")


def _num(s):
    """'$1,097.05' -> 1097.05. Raises on garbage rather than guessing."""
    m = re.search(r"-?[\d,]+(?:\.\d+)?", str(s))
    if not m:
        raise BuildError(f"not a number: {s!r}")
    return float(m.group(0).replace(",", ""))


def derive_metrics(pos: dict, key: str) -> None:
    """Compute every figure that is a pure function of the price and a stored constant.

    These used to be hand-written prose ("still up 173%", "$4.86 trillion", "needs to
    rise 163%") and every one of them was wrong within a week of being typed, because
    the price moved and the prose did not. Deriving them from `base` means they cannot
    disagree with the board — the same price feeds both.

    Stored per position under `base`: year_start (price on Jan 1), high_1y, low_1y,
    cap_usd_at [cap, at_price], eps_at [at_price, pe]. All optional; a metric is only
    derived when its constant exists.
    """
    base = pos.get("base") or {}
    if not base:
        return
    price = _num(pos.get("price", ""))
    m = {}

    if base.get("year_start"):
        ytd = price / float(base["year_start"]) - 1
        if ytd > 1:
            m["ytd_en"] = m["ytd_ko"] = "≈ +%d%%" % round(ytd * 100)
        else:
            m["ytd_en"] = m["ytd_ko"] = "≈ %+.1f%%" % (ytd * 100)

    if base.get("high_1y"):
        hi = float(base["high_1y"])
        dd = 1 - price / hi
        # dd_num is language-neutral (for the board cell); dd_en/ko are worded (facts).
        if dd <= 0.002:
            # Exactly at the high: "0%" — precise, figure-shaped, language-neutral.
            # "≈ 0.0%" hedged an exact fact and read oddly next to "Record close".
            m["dd_num"] = "0%"
            m["dd_en"], m["dd_ko"] = "at its high", "최고가 수준"
        else:
            m["dd_num"] = "≈ %.1f%%" % (dd * 100)
            m["dd_en"] = m["dd_ko"] = m["dd_num"]
        rec = hi / price - 1
        m["recover_en"] = m["recover_ko"] = "≈ +%d%%" % round(rec * 100)

    if base.get("low_1y"):
        lo = float(base["low_1y"])
        m["above_low_en"] = m["above_low_ko"] = "≈ +%.1f%%" % ((price / lo - 1) * 100)
        m["range_en"] = m["range_ko"] = "$%s – $%s" % (
            format(lo, ",.2f"), format(float(base.get("high_1y", lo)), ",.2f"))

    if base.get("cap_usd_at"):
        cap0, at = base["cap_usd_at"]
        cap = float(cap0) * price / float(at)
        m["cap_en"] = "≈ $%.1f trillion" % (cap / 1e12)
        m["cap_ko"] = "≈ %.1f조 달러" % (cap / 1e12)

    if base.get("eps_at"):
        at, pe0 = base["eps_at"]
        pe = float(pe0) * price / float(at)
        m["pe_en"] = m["pe_ko"] = "≈ %.1f×" % pe

    pos["metrics"] = m


def derive_facts(pos: dict, key: str) -> None:
    """Render the facts rows. An item is {en, ko} labels plus EITHER `auto: "<metric>"`
    (build fills the value from derive_metrics, so it can never drift from the price)
    OR manual `v_en`/`v_ko` for genuinely hand-set facts (a date, a historical month)."""
    facts = pos.get("facts")
    if not isinstance(facts, list):
        return
    metrics = pos.get("metrics", {})
    rows = []
    for i, f in enumerate(facts):
        row = dict(f)
        auto = f.get("auto")
        field = f.get("field")
        if field:
            ve, vk = pos.get(field + "_en"), pos.get(field + "_ko")
            if not ve or not vk:
                raise BuildError(f"facts[{i}] of {key!r}: field {field!r} missing _en/_ko")
            row["v_en"], row["v_ko"] = ve, vk
        elif auto:
            ve, vk = metrics.get(auto + "_en"), metrics.get(auto + "_ko")
            if ve is None:
                raise BuildError(f"facts[{i}] of {key!r}: auto metric {auto!r} not derivable "
                                 f"(missing base constant?)")
            row["v_en"], row["v_ko"] = ve, vk
        elif not (f.get("v_en") and f.get("v_ko")):
            raise BuildError(f"facts[{i}] of {key!r}: needs either auto or v_en+v_ko")
        rows.append(row)
    pos["facts_rows"] = rows


def derive_market(data: dict) -> dict:
    """Flatten market.positions into the board's row list.

    The board is a repeat rather than a set of value markers because the direction
    CLASSES change with the data too — a marker can only replace content between two
    comments, so a position that flips from up to down would keep rendering green.
    """
    market = data.get("market")
    if not isinstance(market, dict):
        return data

    # The board's day column was hardcoded "Friday", which is simply wrong for any other
    # session. Derive it from the date the numbers come from. This must happen BEFORE the
    # rows are built, because each row carries a copy for its mobile label.
    DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    DAYS_KO = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    try:
        d = datetime.date.fromisoformat(str(market.get("as_of", ""))[:10])
        market["day_label_en"] = DAYS_EN[d.weekday()]
        market["day_label_ko"] = DAYS_KO[d.weekday()]
    except ValueError:
        market["day_label_en"], market["day_label_ko"] = "Latest", "최근"

    # The masthead leads with the BRIEF's date — the morning it was written — not the
    # session it covers. A Wednesday-morning page headlined "Tuesday, After the Close"
    # reads as stale even when freshly built; a morning paper is dated the day you read
    # it, and the sub-line explains which close it covers. Build time IS write time.
    today = pacific_today()
    DAYS_EN2 = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    DAYS_KO2 = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    MON_EN2 = ["January","February","March","April","May","June","July","August",
               "September","October","November","December"]
    kind_en = "Weekend Recap" if market.get("mode") == "weekend" else "Morning Brief"
    kind_ko = "주말 정리" if market.get("mode") == "weekend" else "아침 브리핑"
    market["brief_date_en"] = "%s, %s %d, %d &middot; %s" % (
        DAYS_EN2[today.weekday()], MON_EN2[today.month-1], today.day, today.year, kind_en)
    market["brief_date_ko"] = "%d년 %d월 %d일 %s · %s" % (
        today.year, today.month, today.day, DAYS_KO2[today.weekday()], kind_ko)

    # The Today block leads "In plain English" with the day the reader is IN. The label
    # comes from the build clock (same as the masthead); the prose (today_en/ko) is
    # agent-written each run. If a run ever fails to write it, fall back to an honest
    # generic line — never an empty box, never yesterday's story dressed as today.
    market["today_label_en"] = "Today · %s, %s %d" % (
        DAYS_EN2[today.weekday()], MON_EN2[today.month-1], today.day)
    market["today_label_ko"] = "오늘 · %d월 %d일 %s" % (
        today.month, today.day, DAYS_KO2[today.weekday()])
    today_stale = str(market.get("today_date", ""))[:10] != today.isoformat()
    if (today_stale
            or not str(market.get("today_en", "")).strip()
            or not str(market.get("today_ko", "")).strip()):
        if today.weekday() >= 5:
            market["today_en"] = ("Markets are closed for the weekend. "
                                  "The week's full story is below.")
            market["today_ko"] = "주말이라 시장은 휴장입니다. 지난 한 주의 이야기가 아래에 있습니다."
        else:
            market["today_en"] = ("Markets are open today. Prices on this page update "
                                  "live through the session; the last session's full "
                                  "story is below.")
            market["today_ko"] = ("오늘 시장은 열려 있습니다. 이 페이지의 가격은 장중 내내 "
                                  "자동으로 갱신되며, 직전 거래일의 자세한 이야기는 아래에 "
                                  "있습니다.")

    # The context label over yesterday's story names the session it retells, so a
    # Wednesday page says "Tuesday, in review" and a weekend page says the week.
    if market.get("mode") == "weekend":
        market["ctx_label_en"] = "The week, in review"
        market["ctx_label_ko"] = "지난 한 주 돌아보기"
    else:
        market["ctx_label_en"] = "%s, in review" % market.get("day_label_en", "The last session")
        market["ctx_label_ko"] = "%s 장 돌아보기" % market.get("day_label_ko", "직전")

    # The methodology note names the session date; derive it so it cannot go stale.
    try:
        dt = datetime.date.fromisoformat(str(market.get("as_of", ""))[:10])
        MON_EN = ["January","February","March","April","May","June","July","August",
                  "September","October","November","December"]
        market["asof_phrase_en"] = "%s, %s %d, %d" % (
            market["day_label_en"], MON_EN[dt.month-1], dt.day, dt.year)
        market["asof_phrase_ko"] = "%d년 %d월 %d일 %s의" % (
            dt.year, dt.month, dt.day, market["day_label_ko"])
    except ValueError:
        market["asof_phrase_en"], market["asof_phrase_ko"] = "the latest session", "최근 거래일의"

    rows = []
    for i, key in enumerate(BOARD_ORDER):
        pos = market.get("positions", {}).get(key)
        if not pos:
            raise BuildError(f"market.positions missing {key!r}")
        # Board cells carry ONLY the figure — "▲ +1.79%", not "▲ +1.79% on Tuesday".
        # The column header already names the session; repeating it in all five rows is
        # what made cells wrap to two ragged lines. Fuller phrasing stays in the panel
        # headers, where there is room for a sentence.
        m2 = re.search(r"[≈\s]*[+\-−]?[\d.]+%", str(pos.get("day_en", "")))
        pos["day_cell"] = (("≈ " if "≈" in str(pos.get("day_en","")) else "") + m2.group(0).strip().lstrip("≈ ").strip()) if m2 else str(pos.get("day_en",""))
        if str(pos.get("day_dir")) == "fl" and not m2:
            pos["day_cell"] = "0.0%"
        m3 = re.search(r"(≈\s*)?[+\-−]?[\d.]+%", str(pos.get("week_en", "")))
        pos["week_cell"] = m3.group(0).strip() if m3 else str(pos.get("week_en",""))
        derive_metrics(pos, key)
        # The board's drawdown column and its panel-fact twin follow the derived value
        # whenever the 1y-high constant exists — one source, not two.
        mtr = pos.get("metrics", {})
        if "dd_num" in mtr:
            pos["drawdown"] = mtr["dd_num"]
            pos["drawdown_fact_en"] = mtr["dd_en"]
            pos["drawdown_fact_ko"] = mtr["dd_ko"]
            if mtr["dd_en"] == "at its high":
                pos["drawdown_arrow"] = ""
                pos["drawdown_dir"] = "fl"
        derive_facts(pos, key)
        row = dict(pos)
        row["key"] = key
        row["current"] = i == 0          # the board opens on the first row
        row["day_label_en"] = market.get("day_label_en", "Latest")
        row["day_label_ko"] = market.get("day_label_ko", "최근")
        # Arrows are legitimately absent (a flat day has none). The drawdown VALUE is not
        # optional — defaulting it to "" rendered a dangling ▼ with no number after it,
        # which is worse than refusing to build.
        for f in ("day_arrow", "week_arrow", "drawdown_arrow"):
            row.setdefault(f, "")
        rows.append(row)
    market["board"] = rows

    # The strip is a repeat for the same reason the board is: its direction classes
    # (up / dn / fl / cau) change with the data, and an F-marker can only replace text
    # between two comments — so a wired-by-marker strip would keep rendering an index
    # green after it turned negative.
    STRIP_ORDER = ("spx", "ndx", "dow", "vix", "us10y", "us30y")
    cells = []
    for key in STRIP_ORDER:
        cell = market.get("strip", {}).get(key)
        if not cell:
            raise BuildError(f"market.strip missing {key!r}")
        c = dict(cell)
        c["key"] = key
        c.setdefault("change_ko", c.get("change_en", ""))
        cells.append(c)
    market["strip_cells"] = cells
    return data


def derive_freshness(data: dict) -> None:
    """Put the page's own age on the page.

    The scheduled job once failed for three days without anyone noticing, because the only
    evidence was a log file. The fix is not a popup — it is making the page say how old it
    is, so staleness is visible at exactly the moment someone is reading it.
    """
    market = data.get("market")
    if not isinstance(market, dict):
        return
    # Key this off the MARKET data only, never the record sweep.
    #
    # An earlier version took the newer of the two. That let a midday record-only sweep
    # report "Updated this morning" while the prices on the board were four days old —
    # the page claiming freshness it did not have, which is worse than showing nothing.
    # The prices are the headline content, so the prices decide the headline age.
    stamp = str(market.get("as_of", ""))[:10]
    try:
        age = (pacific_today() - datetime.date.fromisoformat(stamp)).days
    except ValueError:
        market["fresh_en"] = market["fresh_ko"] = ""
        market["fresh_cls"] = ""
        return

    if age <= 1:
        market["fresh_en"] = "Prices are current"
        market["fresh_ko"] = "최신 시세입니다"
        market["fresh_cls"] = "ok"
    elif age <= 3:
        market["fresh_en"] = "Prices from %d days ago" % age
        market["fresh_ko"] = "%d일 전 시세입니다" % age
        market["fresh_cls"] = "ok"
    else:
        market["fresh_en"] = ("Prices are %d days old — this page has not updated" % age)
        market["fresh_ko"] = ("시세가 %d일 지났습니다 — 페이지가 업데이트되지 않았습니다" % age)
        market["fresh_cls"] = "stale"


EVERGREEN = {
    "spx": [("This is the whole market in one number. When it's up, most things are up.",
             "시장 전체를 숫자 하나로 본 겁니다. 이게 오르면 대부분 같이 오른 거예요."),
            ("If you only look at one number all day, this is a fair one to pick.",
             "하루에 숫자 하나만 보신다면, 이걸 보시면 됩니다.")],
    "qqq": [("The 100 biggest technology names, all in one fund.",
             "큰 기술주 100개를 한 번에 담은 펀드예요."),
            ("Nvidia is its largest holding, so these two move together a lot.",
             "엔비디아 비중이 제일 커서, 이 둘은 같이 움직일 때가 많습니다.")],
    "nvda": [("The price isn't the scary part. Whether the sales are real is.",
              "가격이 문제가 아니라, 매출이 진짜냐가 문제예요."),
             ("Four of your five holdings move with this one company.",
              "보유 다섯 중 넷이 이 회사 하나를 따라 움직입니다.")],
    "soxl": [("Careful with this one. Triple risk, and it resets every single day.",
              "이건 조심하셔야 해요. 세 배짜리라 매일 다시 맞춥니다."),
             ("It moves three times as much as chip stocks — in both directions.",
              "반도체 주식보다 세 배씩 움직입니다. 오를 때도, 내릴 때도요.")],
    "cost": [("Good business, expensive price. That's the whole debate.",
              "사업은 좋고 가격은 비쌉니다. 그게 전부예요."),
             ("People shop here whether times are good or bad. That's the appeal.",
              "형편이 좋든 나쁘든 사람들은 여기서 장을 봅니다. 그게 강점이에요.")],
}

# Clock and live lines carry a {t} slot the page fills with a real local time. They live
# here rather than in the JS so the validation gate can see them like any other prose.
CLOCK_LINES = [
    ("premarket", "The market opens at {t} your time. Nothing here will move until then.",
     "시장은 {t}에 열립니다. 그때까지는 아무것도 움직이지 않아요."),
    ("open30", "It just opened. The first half hour is always the jumpiest — I wouldn't read much into it.",
     "막 열렸어요. 처음 30분은 늘 출렁입니다. 크게 의미 두지 마세요."),
    ("midday", "Trading is open. The prices here refresh every few minutes.",
     "장이 열려 있습니다. 여기 가격은 몇 분마다 새로 들어와요."),
    ("lasthour", "Last hour of trading. This is what sets the closing price you'll read tomorrow.",
     "장 마지막 한 시간입니다. 내일 아침에 보실 종가가 지금 정해집니다."),
    ("closed", "Trading is done for today. These are the final prices.",
     "오늘 거래는 끝났습니다. 이게 최종 가격이에요."),
    ("weekend", "The market is closed for the weekend. Nothing changes until Monday.",
     "주말이라 시장은 쉽니다. 월요일까지 바뀌는 건 없어요."),
    ("holiday", "The market is closed today for a holiday. Nothing has changed since it last traded.",
     "오늘은 휴장일입니다. 마지막 거래일 이후로 바뀐 게 없어요."),
]

LIVE_LINES = [
    ("allup", "Everything you own is up today.", "오늘은 보유 종목이 전부 올랐습니다."),
    ("alldown", "Everything you own is down today.", "오늘은 보유 종목이 전부 내렸습니다."),
    ("split", "A split day — some of yours up, some down.",
     "오늘은 엇갈립니다. 오른 것도 있고 내린 것도 있어요."),
    ("quiet", "Nothing here has moved even half a percent today.",
     "오늘은 여기 있는 것 중 0.5%도 움직인 게 없습니다."),
]


def _pct_words(s: str) -> str:
    """'≈ 54.0%' -> '54%' — Pancho speaks, so he rounds and drops the hedge glyph."""
    m = re.search(r"([\d.]+)", str(s))
    if not m:
        return ""
    return "%d%%" % round(float(m.group(1)))


# The market calendar, in one place. The page used to carry a 2026-only holiday list
# inside its JS, which would have had Pancho announcing an open market on New Year's Day
# 2027, and it treated every day as a full session — so the status chip read "Market open
# now" from 1pm to 4pm Eastern on the three early-close days. Years absent from CAL make
# the page say nothing rather than guess.
MARKET_CAL = {
    2026: {"holidays": ["2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03",
                        "2026-05-25", "2026-06-19", "2026-07-03", "2026-09-07",
                        "2026-11-26", "2026-12-25"],
           "half_days": ["2026-11-27", "2026-12-24"]},
    2027: {"holidays": ["2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26",
                        "2027-05-31", "2027-06-18", "2027-07-05", "2027-09-06",
                        "2027-11-25", "2027-12-24"],
           "half_days": ["2027-11-26"]},
}


def derive_pancho(data: dict) -> None:
    """Build Pancho's line ledger.

    His lines used to be a hardcoded table inside <script>, which put them outside every
    guard the page has (check_invariants strips <script> before it counts anything) and
    let them name dates that had already passed. Now every line is a record with an
    owner, a tier and an expiry, generated here where the figures come from, so a line
    can never outlive the fact behind it.

    Tiers, highest priority first: notable (a live event), live (computed in-page from
    the quote feed), clock (time of day), today (written by the scheduled runs), figure
    (derived from price + base), evergreen (permanent floor, no figures, never expires).
    """
    market = data.get("market")
    if not isinstance(market, dict):
        return
    today = pacific_today().isoformat()
    lines = []

    def add(tier, pos, en, ko, expires="", lid=""):
        if not en or not ko:
            return
        lines.append({"id": lid or ("%s-%s-%d" % (tier, pos or "all", len(lines))),
                      "tier": tier, "pos": pos, "expires": expires,
                      "en": en.strip(), "ko": ko.strip()})

    for key in BOARD_ORDER:
        pos = market.get("positions", {}).get(key) or {}
        m = pos.get("metrics") or {}
        name_en = pos.get("name_en", key.upper())
        name_ko = pos.get("name_ko", name_en)

        # Figure lines are regenerated from the current price every build, so they are
        # true by construction and need no expiry.
        dd, rec = m.get("dd_num", ""), m.get("recover_en", "")
        if dd == "0%":
            add("figure", key,
                "It's right at the highest price it has reached in a year.",
                "지난 1년 중 가장 높은 가격에 와 있습니다.")
        elif dd and rec:
            add("figure", key,
                "It's about %s below its high from last year. Getting back there means rising about %s."
                % (_pct_words(dd), _pct_words(rec)),
                "작년 고점보다 약 %s 아래입니다. 거기까지 가려면 약 %s 올라야 해요."
                % (_pct_words(dd), _pct_words(rec)))

        ytd = m.get("ytd_en", "")
        if ytd:
            up = "-" not in ytd and "−" not in ytd
            add("figure", key,
                "So far this year it's %s about %s." % ("up" if up else "down", _pct_words(ytd)),
                "올해 들어 약 %s %s." % (_pct_words(ytd), "올랐습니다" if up else "내렸습니다"))

        pe = m.get("pe_en", "")
        if pe:
            add("figure", key,
                "Its price is about %s a year of profits. That's the expensive part."
                % _pct_words(pe).replace("%", " times"),
                "주가가 한 해 이익의 약 %s배입니다. 비싸다는 얘기가 여기서 나와요."
                % _pct_words(pe).replace("%", ""))

        for en, ko in EVERGREEN.get(key, []):
            add("evergreen", key, en, ko)

    # Lines the scheduled runs write themselves: one for the morning, one for the
    # afternoon. They expire with the day they were written for, so a failed run can
    # never leave yesterday's remark in the dog's mouth.
    for slot in ("pancho_am", "pancho_pm"):
        blk = market.get(slot) or {}
        if isinstance(blk, dict) and blk.get("en") and blk.get("ko"):
            if str(blk.get("date", ""))[:10] == today:
                add("today", blk.get("pos", ""), blk["en"], blk["ko"], expires=today, lid=slot)

    for lid, en, ko in CLOCK_LINES:
        add("clock", "", en, ko, lid="clock-" + lid)
    for lid, en, ko in LIVE_LINES:
        add("live", "", en, ko, lid="live-" + lid)

    # Structural gate. A malformed ledger must stop the build here, not surface as a dog
    # with an empty speech bubble that nobody notices for a week.
    seen = set()
    for ln in lines:
        if ln["id"] in seen:
            raise BuildError("pancho: duplicate line id %r" % ln["id"])
        seen.add(ln["id"])
        for lg in ("en", "ko"):
            if "<" in ln[lg] or ">" in ln[lg] or "&" in ln[lg]:
                raise BuildError("pancho line %r (%s): the bubble is written with "
                                 "textContent, so markup and entities render literally"
                                 % (ln["id"], lg))
        # Korean runs shorter than English at the same meaning; one cap would either
        # let Korean overflow the bubble or strangle the English.
        if len(ln["en"]) > 125:
            raise BuildError("pancho line %r: English is %d chars (max 125)"
                             % (ln["id"], len(ln["en"])))
        if len(ln["ko"]) > 70:
            raise BuildError("pancho line %r: Korean is %d chars (max 70)"
                             % (ln["id"], len(ln["ko"])))
    if not any(l["tier"] == "evergreen" for l in lines):
        raise BuildError("pancho: no evergreen lines — the fallback floor is gone")

    # Thresholds for the notable tier, which the page evaluates against the live feed.
    # A "big move" has to mean something different per position: 4% is a dramatic day
    # for Nvidia and an ordinary one for a 3x fund, and one shared number would either
    # cry wolf about SOXL daily or never fire for Costco.
    BIG = {"spx": 1.5, "qqq": 2.0, "nvda": 4.0, "soxl": 8.0, "cost": 3.0}
    # Short names, because these get read inside a sentence. The board's name_en is a
    # description ("Nvidia — makes AI chips"), which is right in a table cell and wrong
    # in "... is the highest it has been in a year".
    # The Korean name carries its own subject particle: 이 after a closing consonant,
    # 가 after a vowel. Gluing one particle onto every name in the template produces
    # "SOXL가", which is simply wrong Korean, and the page has one reader who would
    # notice immediately.
    SPOKEN = {"spx": ("The S&P 500", "S&P 500 지수가"),
              "qqq": ("QQQ", "QQQ가"),
              "nvda": ("Nvidia", "엔비디아가"),
              "soxl": ("SOXL", "SOXL이"),
              "cost": ("Costco", "코스트코가")}
    trig = {}
    for key in BOARD_ORDER:
        pos = market.get("positions", {}).get(key) or {}
        base = pos.get("base") or {}
        nm = SPOKEN.get(key, (key.upper(), key.upper()))
        t = {"big": BIG.get(key, 3.0), "en": nm[0], "ko": nm[1]}
        if base.get("high_1y"):
            t["hi"] = float(base["high_1y"])
        if base.get("low_1y"):
            t["lo"] = float(base["low_1y"])
        trig[key] = t
    market["pancho_trig_json"] = json.dumps(trig, ensure_ascii=False, separators=(",", ":"))

    market["pancho_json"] = json.dumps(lines, ensure_ascii=False, separators=(",", ":"))
    market["pancho_count"] = len(lines)
    market["market_cal_json"] = json.dumps(MARKET_CAL, separators=(",", ":"))


def derive(data: dict) -> dict:
    """Turn stored data into the display fields the template needs. Kept here, in data
    space, so the research job only ever writes facts and never markup."""
    derive_market(data)
    derive_freshness(data)
    derive_pancho(data)   # after derive_market: it reads the metrics that loop computes
    VERB = {
        "said":   ("Said",   "발언"),
        "did":    ("Did",    "조치"),
        "bought": ("Bought", "매수"),
    }
    trump = data.get("trump")
    if not isinstance(trump, dict):
        return data

    # A dated record whose dates are out of order is not a record. Sort here rather than
    # trusting whatever order the research step happened to write them in.
    trump["entries"] = sorted(
        trump.get("entries", []), key=lambda e: e.get("date", ""), reverse=True
    )

    for e in trump.get("entries", []):
        en, ko = VERB.get(e.get("verb", ""), ("Noted", "기록"))
        e["verb_en"], e["verb_ko"] = en, ko

        hits = [t for t in e.get("touches", []) if t in POS_LABEL]
        e["touches_n"] = len(hits)
        if hits:
            names = ", ".join(POS_LABEL[t] for t in hits)
            e["touches_en"] = f"Touches {names} — {len(hits)} of the 5"
            e["touches_ko"] = f"{names} 관련 — 다섯 중 {len(hits)}개"
        else:
            e["touches_en"] = e["touches_ko"] = ""

        # Only entries with a real measured number get the reaction line at all.
        e.setdefault("reaction_en", "")
        e.setdefault("reaction_ko", "")
        e.setdefault("reaction_dir", "")
        e["reaction_arrow"] = {"up": "▲", "down": "▼", "dn": "▼"}.get(e.get("reaction_dir", ""), "")
        e.setdefault("quote", "")
        e.setdefault("quote_ko", "")
        e.setdefault("ticker", "")

    # The footprint strip: which of the five anything on the current record reaches.
    # Lit means "something here affects this holding", so the reader can see at a glance
    # that chip policy hits four of five while the Dell episode hits none of them.
    touched = set()
    for e in trump.get("entries", []):
        touched.update(t for t in e.get("touches", []) if t in POS_LABEL)
    trump["footprint"] = [
        {"label": POS_LABEL[k], "cls": "on" if k in touched else "",
         # A filled vs hollow dot so the lit state does not ride on hue alone.
         "mark": "\u25cf" if k in touched else "\u25cb",
         "state_en": "affected" if k in touched else "not affected",
         "state_ko": "영향 있음" if k in touched else "영향 없음"}
        for k in ("spx", "qqq", "nvda", "soxl", "cost")
    ]

    # The reading line is DERIVED, never hand-written — a hand-written one had already
    # drifted, naming a January item as the most recent while a June item sat above it.
    #
    # It leads with the RECORD, not with the five positions. This section is a log of what
    # the President says about any company — magnets, computers, chipmakers, his own media
    # firm. An earlier version opened with "Nothing touches the five positions", which read
    # as though the whole section were a filter on the portfolio and made the other entries
    # look like padding. Exposure to the five is real information, so it still gets a
    # sentence — second, where it belongs.
    hits = [e for e in trump["entries"] if e.get("touches")]
    entries = trump["entries"]
    checked = trump.get("checked", "")

    if entries:
        newest = entries[0]                    # sorted newest-first above
        n = len(entries)
        lead_en = "%d entries on record. Newest: %s — %s%s." % (
            n, newest["date_en"], newest["headline"][0].lower() + newest["headline"][1:]
            if len(newest["headline"]) > 1 and newest["headline"][1].islower() else newest["headline"], "")
        lead_ko = "기록 %d건. 가장 최근은 %s, %s 관련입니다." % (
            n, newest["date_ko"], newest.get("company_ko", ""))
    else:
        lead_en, lead_ko = "Nothing on record yet.", "아직 기록이 없습니다."

    if hits:
        newest_hit = hits[0]
        names = sorted({POS_LABEL[t] for e in hits for t in e["touches"] if t in POS_LABEL},
                       key=lambda x: ("SPX", "QQQ", "NVDA", "SOXL", "COST").index(x))
        tail_en = " Of these, %d reach what you hold — %s. Most recent: %s." % (
            len(hits), ", ".join(names), newest_hit["date_en"])
        tail_ko = " 이 가운데 %d건이 보유 종목(%s)과 관련이 있고, 가장 최근은 %s입니다." % (
            len(hits), ", ".join(names), newest_hit["date_ko"])
    else:
        tail_en = " None of them reach the five positions."
        tail_ko = " 이 가운데 다섯 종목과 관련된 것은 없습니다."

    trump["reading_en"] = lead_en + tail_en
    trump["reading_ko"] = lead_ko + tail_ko
    return data


def apply_repeats(src: str, data: dict) -> tuple:
    count = 0

    def sub(m):
        nonlocal count
        name, block = m.group(1), m.group(2)
        items = dotted(data, name)
        if not isinstance(items, list):
            raise BuildError(f"repeat {name!r}: data is {type(items).__name__}, expected list")
        rendered = "".join(render_placeholders(block, it, name) for it in items)
        count += 1
        return f"<!--R:{name}-->{rendered}<!--/R-->"

    return REPEAT_RE.sub(sub, src), count


def apply_fields(src: str, data: dict) -> tuple:
    count = 0

    def sub(m):
        nonlocal count
        key, raw = m.group(1), m.group(2)
        val = str(dotted(data, key))
        count += 1
        if raw == "|js":
            # Script payloads (the Pancho ledger, the market calendar) get NO wrapper
            # comments. `<!--` inside a script is a legal single-line comment in every
            # browser, so the usual marker would comment out the rest of the line and
            # take the value with it — the page would load with an undefined ledger.
            if "</" in val or "<!--" in val:
                raise BuildError(f"{key}: script payload contains a tag-like sequence")
            return val
        if raw == "|raw":
            # Prose fields carry inline <b>. Safety is enforced at the validation gate,
            # which rejects any tag other than <b> in agent-written prose — escaping
            # here would print the tags as literal text, which run 2 briefly shipped.
            return f"<!--F:{key}|raw-->{val}<!--/F-->"
        # Neutralise angle brackets so a stray value can never open a tag. `&` is left
        # alone on purpose: these fields legitimately carry entities like &nbsp; and
        # &middot; from the dateline, and escaping those would print them literally.
        val = val.replace("<", "&lt;").replace(">", "&gt;")
        return f"<!--F:{key}-->{val}<!--/F-->"

    return FIELD_RE.sub(sub, src), count


def load_data() -> dict:
    """Merge every data/*.json into one namespace keyed by filename."""
    if not DATA.exists():
        raise BuildError(f"no data directory at {DATA}")
    merged = {}
    for path in sorted(DATA.glob("*.json")):
        try:
            merged[path.stem.replace("-", "_")] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise BuildError(f"{path.name} is not valid JSON: {e}")
    if not merged:
        raise BuildError("data/ contains no .json files")
    return merged


STYLE_SCRIPT_RE = re.compile(r"<(style|script)\b[^>]*>.*?</\1>", re.S | re.I)


def check_invariants(before: str, after: str):
    """The properties that must survive every build. A violation aborts the write."""
    problems = []

    # Count language attributes in MARKUP only. A CSS selector like
    # td[data-en="Price"] or a JS string would otherwise register as a stray twin and
    # fail an otherwise-correct build.
    markup = STYLE_SCRIPT_RE.sub("", after)

    en = len(re.findall(r'data-l="en"', markup))
    ko = len(re.findall(r'data-l="ko"', markup))
    if en != ko:
        problems.append(f"bilingual parity broken: {en} EN blocks vs {ko} KO blocks")

    m_en = len(re.findall(r"data-en=", markup))
    m_ko = len(re.findall(r"data-ko=", markup))
    if m_en != m_ko:
        problems.append(f"mobile label parity broken: {m_en} data-en vs {m_ko} data-ko")

    idx = after.encode("utf-8").find(b"charset")
    if idx == -1 or idx > 1024:
        problems.append("meta charset missing from the first 1024 bytes (Korean will mojibake on iOS)")

    for tag in ("script", "style", "table", "section", "main"):
        o = len(re.findall(rf"<{tag}\b", after, re.I))
        c = len(re.findall(rf"</{tag}>", after, re.I))
        if o != c:
            problems.append(f"unbalanced <{tag}>: {o} open, {c} close")

    for bad in ("<!DOCTYPE", "<html", "<head>", "<body"):
        if bad.lower() in after.lower():
            problems.append(f"{bad} present — breaks the Artifact build")

    # Pancho must render and must be able to speak. The old check here grepped for
    # `var IDLE`, which stopped existing when the sprite moved to base64 FRAMES — so it
    # matched nothing and passed every build on an empty set for months. Check the two
    # things that are actually true of a working dog now.
    frames = re.search(r"var FRAMES\s*=\s*\{(.*?)\}\s*;", after, re.S)
    if not frames:
        problems.append("sprite FRAMES block missing — Pancho will not render")
    else:
        srcs = re.findall(r'"(data:image/[^"]+)"', frames.group(1))
        if not srcs:
            problems.append("sprite FRAMES carries no embedded images")
        elif any(len(s) < 200 for s in srcs):
            problems.append("a sprite frame is suspiciously small — likely a truncated image")

    lm = re.search(r"var PLINES\s*=\s*(\[.*?\]);", after, re.S)
    if not lm:
        problems.append("Pancho line ledger (PLINES) missing — the bubble would be empty")
    else:
        try:
            pl = json.loads(lm.group(1))
        except ValueError as e:
            problems.append(f"Pancho line ledger is not valid JSON: {e}")
        else:
            if not [x for x in pl if x.get("tier") == "evergreen"]:
                problems.append("Pancho ledger has no evergreen line — no fallback floor")
            for x in pl:
                if not x.get("en") or not x.get("ko"):
                    problems.append(f"Pancho line {x.get('id')!r} is missing a twin")

    # A build that shrinks the page by a third has eaten something.
    if len(after) < len(before) * 0.66:
        problems.append(f"output shrank suspiciously: {len(before):,} -> {len(after):,} bytes")

    if problems:
        raise BuildError("invariant check failed:\n  - " + "\n  - ".join(problems))


def main():
    if not TEMPLATE.exists():
        raise BuildError(f"{TEMPLATE} not found")

    src = TEMPLATE.read_text(encoding="utf-8")
    data = derive(load_data())

    out, n_rep = apply_repeats(src, data)
    out, n_fld = apply_fields(out, data)

    check_invariants(src, out)

    if re.search(r"\{\{", out):
        raise BuildError("unrendered {{placeholders}} remain in the output")

    prev = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else None
    if prev == out:
        print("build: no change (page already matches the data)")
    else:
        if prev is not None:
            BACKUPS.mkdir(exist_ok=True)
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.copy2(OUTPUT, BACKUPS / f"dashboard.{stamp}.html")
        OUTPUT.write_text(out, encoding="utf-8")
        print(f"build: rendered {n_fld} fields, {n_rep} repeat blocks -> dashboard.html "
              f"({len(out.encode()):,} bytes)")

    # Keep the last 30 backups; this runs every weekday.
    olds = sorted(BACKUPS.glob("dashboard.*.html"))
    for p in olds[:-30]:
        p.unlink()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BuildError as e:
        print(f"BUILD REFUSED: {e}", file=sys.stderr)
        print("Previous dashboard.html left untouched.", file=sys.stderr)
        sys.exit(1)
