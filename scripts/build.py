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

FIELD_RE = re.compile(r"<!--F:([a-zA-Z0-9_.\-]+)(\|raw)?-->(.*?)<!--/F-->", re.S)
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
        m["dd_num"] = "≈ %.1f%%" % (max(dd, 0) * 100)
        if dd <= 0.002:
            m["dd_en"], m["dd_ko"] = "at its high", "최고가 수준"
        else:
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
    today = datetime.date.today()
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
        age = (datetime.date.today() - datetime.date.fromisoformat(stamp)).days
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


def derive(data: dict) -> dict:
    """Turn stored data into the display fields the template needs. Kept here, in data
    space, so the research job only ever writes facts and never markup."""
    derive_market(data)
    derive_freshness(data)
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
        if raw:
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

    # Sprite rows must stay square or the dog renders misshapen.
    m = re.search(r"var IDLE\s*=\s*\[(.*?)\]\s*;", after, re.S)
    if m:
        rows = re.findall(r'"([^"]*)"', m.group(1))
        widths = {len(r) for r in rows}
        if len(widths) > 1:
            problems.append(f"sprite rows are ragged: widths {sorted(widths)}")

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
