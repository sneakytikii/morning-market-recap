#!/bin/bash
# The morning refresh. Invoked by launchd on weekday mornings before the open, and on
# Saturday for the weekend recap.
#
#   ./scripts/refresh.sh weekday
#   ./scripts/refresh.sh weekend
#
# Division of labour, deliberately:
#   Claude    researches and writes data/*.json ONLY. It gets a narrow tool allowlist —
#             search, fetch, and file edits. No Bash. An unattended job should not have a
#             shell.
#   Python    renders the data into the page and refuses to write if any invariant breaks.
#   git       publishes.
#
# If any stage fails the previous page stays live. A stale correct page beats a fresh
# broken one, and this runs while nobody is watching.

set -uo pipefail

export PATH="$HOME/.local/bin:$HOME/.nvm/versions/node/v24.18.0/bin:/usr/bin:/bin:/usr/sbin:/sbin"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# weekday — the previous close, before the open
# weekend — the week, on Saturday
# tracker — midday sweep of the record section only; leaves market numbers alone
MODE="${1:-weekday}"
# Pacific, not machine-local: the reader's day (dad, PST) is the day that counts, and
# it must agree with build.py's pacific_today() or the staleness stamps drift.
TODAY_STAMP="$(TZ=America/Los_Angeles date +%Y-%m-%d)"
case "$MODE" in
  weekday|weekend|tracker) ;;
  *) echo "unknown mode: $MODE (expected weekday, weekend or tracker)"; exit 2 ;;
esac
LOG_DIR="$ROOT/.state/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/refresh-$(date +%Y%m%d-%H%M)-$MODE.log"

exec > >(tee -a "$LOG") 2>&1

echo "=============================================================="
echo "Morning Market Recap — $MODE refresh — $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "=============================================================="

# On failure, record it where the PAGE can show it. No system notifications: osascript
# alerts are attributed to "Script Editor", so a background job popping them looks like
# malware rather than like this project. Staleness belongs on the dashboard, where it is
# seen exactly when it matters.
fail() {
  echo "FAILED at: $1"
  echo "Previous dashboard left untouched."
  printf '%s\n%s\n' "$(date '+%Y-%m-%d %H:%M')" "$1" > "$ROOT/.state/last-failure.txt"
  exit 1
}

# --- Single-instance lock -----------------------------------------------------
# Without this, a research step that runs long (the first real run took over 20
# minutes) is still going when the next scheduled job fires, and two agents edit the
# same JSON at once. mkdir is atomic on every filesystem that matters here.
LOCK="$ROOT/.state/refresh.lock"

# A lock that outlives its process would block every future run forever — the failure
# mode where the feature dies silently and nobody notices for weeks. The EXIT trap covers
# ordinary exits and the watchdog, but not SIGKILL or a power cut, so anything older than
# the watchdog ceiling plus slack is treated as debris and cleared.
STALE_AFTER=45   # minutes; the watchdog kills research at 30
if [ -d "$LOCK" ]; then
  # Age alone is not evidence of death, and acting on it is worse than waiting: a run
  # that is still researching (3 attempts x 30m) or still waiting for GitHub to serve
  # the page can legitimately outlive this window, and clearing the lock under it would
  # start a second run writing the same JSON. Ask the operating system whether the
  # process is actually alive; only fall back to age when the pid is gone or unreadable.
  LOCK_PID="$(cat "$LOCK/pid" 2>/dev/null)"
  if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
    echo "Another refresh (pid $LOCK_PID) is still alive. Exiting without changes."
    exit 0
  fi
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +$STALE_AFTER 2>/dev/null)" ]; then
    echo "Clearing a stale lock (pid gone, older than ${STALE_AFTER}m — previous run died without cleaning up)."
    rm -rf "$LOCK"
  fi
fi

if ! mkdir "$LOCK" 2>/dev/null; then
  echo "Another refresh is already running (lock: $LOCK). Exiting without changes."
  exit 0
fi
echo "$$" > "$LOCK/pid"

# Hold the Mac awake for as long as this script runs.
#
# The scheduled wake gets the machine up, but with the lid closed macOS may drop straight
# back to sleep — and the research step takes 20+ minutes. Without this the job can start
# and then be suspended mid-run, which looks identical to a failure.
#
# -i prevents idle sleep; -w ties the caffeinate process's life to this script's PID, so
# it releases the moment the run finishes rather than pinning the Mac awake indefinitely.
/usr/bin/caffeinate -i -w $$ &
# rm -rf, not rmdir: the lock now holds a pid file, and rmdir would fail on a non-empty
# directory and leave the lock behind — reintroducing exactly the bug this guards against.
trap 'rm -rf "$LOCK" 2>/dev/null' EXIT INT TERM

# --- 0a. Already succeeded today? -----------------------------------------------
# The schedule now has multiple slots per mode (a failed 6:12 gets another go at 6:57
# and 7:42). A slot that fires after a success must cost nothing.
STAMP="$ROOT/.state/last-success-$MODE"
if [ -f "$STAMP" ] && [ "$(cat "$STAMP" 2>/dev/null)" = "$TODAY_STAMP" ]; then
  echo "Already ran successfully today ($MODE). Nothing to do."
  exit 0
fi

# --- 0. Don't research a market that hasn't moved ------------------------------
# US market holidays land on weekdays; on those days there is no new close to report.
# Keep this in step with MARKET_CAL in scripts/build.py, which the page reads. This
# list was 2026-only, so from January 2027 the job would have burned a research run on
# every market holiday and published a "brief" about a day that never traded.
HOLIDAYS_2026="2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19 2026-07-03 2026-09-07 2026-11-26 2026-12-25 2027-01-01 2027-01-18 2027-02-15 2027-03-26 2027-05-31 2027-06-18 2027-07-05 2027-09-06 2027-11-25 2027-12-24"
TODAY="$TODAY_STAMP"
if [[ "$MODE" != "weekend" && "$HOLIDAYS_2026" == *"$TODAY"* ]]; then
  echo "Market holiday ($TODAY) — nothing new to report. Skipping."
  exit 0
fi

# --- 1. Research -------------------------------------------------------------
PROMPT_FILE="$ROOT/scripts/prompts/refresh-$MODE.md"
[ -f "$PROMPT_FILE" ] || fail "missing prompt file $PROMPT_FILE"

echo
echo "--- 0.5  Waiting for network ---"
NET_OK=0
for i in $(seq 1 30); do
  if /usr/bin/curl -Is --max-time 8 https://api.anthropic.com >/dev/null 2>&1; then
    NET_OK=1; echo "  network up (attempt $i)"; break
  fi
  sleep 10
done
[ "$NET_OK" = "1" ] || fail "no network after 5 minutes"

echo
echo "--- 1/4  Researching (the slow part; the first real run took over 20 minutes) ---"

# Fingerprint everything the research step is NOT allowed to touch. The prompt tells it
# to write data/*.json only, but a prompt is a request, not a boundary — so the write
# scope is restricted below AND verified afterwards.
MANIFEST="$ROOT/.state/manifest-before.txt"
find "$ROOT" -type f \( -name '*.html' -o -name '*.py' -o -name '*.sh' -o -name '*.md' \) \
  -not -path "*/.state/*" -not -path "*/backups/*" -not -path "*/.git/*" \
  -not -path "*/data/*" \
  -exec shasum -a 256 {} \; 2>/dev/null | sort > "$MANIFEST"

RESEARCH_TIMEOUT=1800   # 30 minutes; a hung agent must not eat the whole day

RC=1
for ATTEMPT in 1 2 3; do
  [ "$ATTEMPT" -gt 1 ] && { echo "  retry $ATTEMPT after 90s (last exit $RC)"; sleep 90; }
  claude -p "$(cat "$PROMPT_FILE")" \
        --allowedTools WebSearch WebFetch Read "Edit(data/**)" \
        --add-dir "$ROOT/data" \
        --output-format text &
  CPID=$!
  ( sleep "$RESEARCH_TIMEOUT"; kill -TERM "$CPID" 2>/dev/null ) &
  WPID=$!
  wait "$CPID"; RC=$?
  kill "$WPID" 2>/dev/null; wait "$WPID" 2>/dev/null
  [ "$RC" -eq 0 ] && break
  [ "$RC" -ge 143 ] && echo "  (exit $RC — killed by the ${RESEARCH_TIMEOUT}s watchdog)"
done
[ "$RC" -eq 0 ] || fail "research step failed after 3 attempts (last exit $RC)"

# Did it stay inside data/?
find "$ROOT" -type f \( -name '*.html' -o -name '*.py' -o -name '*.sh' -o -name '*.md' \) \
  -not -path "*/.state/*" -not -path "*/backups/*" -not -path "*/.git/*" \
  -not -path "*/data/*" \
  -exec shasum -a 256 {} \; 2>/dev/null | sort > "$ROOT/.state/manifest-after.txt"
if ! diff -q "$MANIFEST" "$ROOT/.state/manifest-after.txt" >/dev/null; then
  echo "  The research step modified files outside data/:"
  diff "$MANIFEST" "$ROOT/.state/manifest-after.txt" | grep '^[<>]' | awk '{print "    " $NF}' | sort -u
  fail "research step wrote outside data/"
fi

# --- 2. Validate the data before it can touch the page -----------------------
# The run knows which kind of run it is; the agent should not have to remember. The
# weekend prompt sets mode="weekend" and nothing ever cleared it, so the first weekday
# masthead after a Saturday read "Morning Brief"... or rather "Weekend Recap", for as
# long as it took someone to notice. Stamp it from $MODE and the question closes.
python3 - "$MODE" <<'PY'
import json, sys, pathlib
mode = "weekend" if sys.argv[1] == "weekend" else "weekday"
p = pathlib.Path("data/market.json")
d = json.loads(p.read_text(encoding="utf-8"))
if d.get("mode") != mode:
    d["mode"] = mode
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  mode corrected to {mode!r}")
PY

echo
echo "--- 2/4  Validating data ---"
if ! python3 - <<'PY'
import json, re, sys, pathlib, datetime, zoneinfo
root = pathlib.Path.cwd()
ok = True
# The reader's day (Pacific), matching build.py's pacific_today(). A date check against
# the build machine's clock would reject a correct line written either side of midnight.
TODAY = datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).date().isoformat()

def bad(msg):
    global ok
    print(f"  {msg}"); ok = False

def check_twins(obj, path=""):
    """Every *_en string must have a non-empty *_ko twin, and vice versa. This is the
    check that actually protects the bilingual guarantee — the build only counts DOM
    nodes, which stay balanced even when a Korean field is written empty.

    A MISSING twin counts as empty. An earlier version tested `if ko in obj and ...`,
    which meant the exact failure this exists to catch — the research step writing
    English and no Korean at all — passed validation silently."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.endswith("_en"):
                ko = k[:-3] + "_ko"
                if bool(str(v).strip()) != bool(str(obj.get(ko, "")).strip()):
                    bad(f"{path}{k}: no matching {ko} (or one of the pair is empty)")
            elif k.endswith("_ko"):
                # `quote_ko` pairs with a bare `quote`, not `quote_en`: a verbatim quote
                # stays in its original language in both modes, with the Korean rendering
                # offered alongside it rather than replacing it.
                stem = k[:-3]
                if stem not in obj and (stem + "_en") not in obj and str(v).strip():
                    bad(f"{path}{k}: no matching {stem}_en or {stem}")
            check_twins(v, f"{path}{k}.")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check_twins(v, f"{path}[{i}].")

for name in ("market.json", "trump.json"):
    p = root / "data" / name
    if not p.exists():
        bad(f"MISSING data/{name}"); continue
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        bad(f"data/{name} is not valid JSON: {e}"); continue
    print(f"  data/{name}: parses ({len(json.dumps(d)):,} bytes)")
    check_twins(d)

    if name == "trump.json":
        for i, e in enumerate(d.get("entries", [])):
            for req in ("date", "source_url", "headline", "text_en", "text_ko"):
                if not e.get(req):
                    bad(f"trump.json entry {i} ({e.get('date','?')}) missing {req!r}")
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(e.get("date", ""))):
                bad(f"trump.json entry {i}: date is not YYYY-MM-DD")
            if not str(e.get("source_url", "")).startswith("http"):
                bad(f"trump.json entry {i}: source_url is not a URL")
            # A source published before the event cannot be a source for it.
            m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", str(e.get("source_url", "")))
            if m and e.get("date"):
                try:
                    src = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    if src < datetime.date.fromisoformat(e["date"]):
                        bad(f"trump.json entry {i} ({e['date']}): source URL is dated "
                            f"{src} — before the event it cites")
                except ValueError:
                    pass

    if name == "market.json":
        # Raw-rendered prose fields may carry inline <b> and nothing else. This is the
        # gate the |raw render path depends on for safety.
        def check_tags(val, where):
            for tag in re.findall(r"</?([a-zA-Z][a-zA-Z0-9]*)", str(val)):
                if tag.lower() != "b":
                    bad(f"{where}: tag <{tag}> not allowed in prose (only <b>)")
        for k2, pos2 in (d.get("positions") or {}).items():
            for f2 in ("plain_en","plain_ko","verdict_en","verdict_ko",
                       "bull_en","bull_ko","bear_en","bear_ko"):
                if pos2.get(f2): check_tags(pos2[f2], f"positions.{k2}.{f2}")
            for lst in ("news_en","news_ko"):
                for j, it in enumerate(pos2.get(lst) or []):
                    check_tags(it.get("tx",""), f"positions.{k2}.{lst}[{j}]")
        for j, para in enumerate(d.get("lede") or []):
            check_tags(para.get("en",""), f"lede[{j}].en")
            check_tags(para.get("ko",""), f"lede[{j}].ko")
        for f2 in ("next_session_en_html","next_session_ko_html","today_en","today_ko"):
            if d.get(f2): check_tags(d[f2], f2)
        # The Today paragraph is only rendered if today_date matches the build day —
        # otherwise the build silently swaps in a generic fallback. Without this check a
        # run could research the day properly, forget the stamp, and publish the canned
        # line instead, with nothing anywhere reporting that it happened.
        if d.get("today_en") or d.get("today_ko"):
            if str(d.get("today_date", ""))[:10] != TODAY:
                bad(f"market.json today_date is {d.get('today_date')!r}, not today "
                    f"({TODAY}) — the Today paragraph would be discarded for the "
                    f"generic fallback")
            if not d.get("today_en") or not d.get("today_ko"):
                bad("market.json: today_en and today_ko must both be written")

        # Pancho's bubble is written with textContent, so ANY markup renders as literal
        # angle brackets — the <b> that prose is allowed is forbidden here. His lines
        # are also length-capped: the bubble has no scrollbar, it just overflows.
        for slot in ("pancho_am", "pancho_pm"):
            blk = d.get(slot)
            if not blk:
                continue
            if not isinstance(blk, dict):
                bad(f"market.json {slot}: must be an object with date/pos/en/ko")
                continue
            # A date in the PAST is normal, not an error: the morning run does not
            # rewrite the afternoon line, so yesterday's pancho_pm is still sitting here
            # and derive_pancho drops it on sight. Only a missing, malformed or future
            # date is a real problem, and a line the build will DISCARD must never be
            # allowed to fail the publish — otherwise one oversized remark freezes the
            # page for everyone the following morning.
            stamp = str(blk.get("date", ""))[:10]
            try:
                when = datetime.date.fromisoformat(stamp)
            except ValueError:
                bad(f"market.json {slot}: date {blk.get('date')!r} is not an ISO date — "
                    f"the build cannot tell whether this line is current")
                continue
            if when > datetime.date.fromisoformat(TODAY):
                bad(f"market.json {slot}: date {stamp} is in the future")
                continue
            if stamp != TODAY:
                continue     # yesterday's line: the build ignores it, so we do too
            if not blk.get("en") or not blk.get("ko"):
                bad(f"market.json {slot}: needs both en and ko")
            if blk.get("pos") and blk["pos"] not in ("spx","qqq","nvda","soxl","cost"):
                bad(f"market.json {slot}: pos {blk['pos']!r} is not one of the five")
            for lg, cap in (("en", 120), ("ko", 65)):
                v = str(blk.get(lg, ""))
                # Angle brackets only. "&" is fine — the bubble is textContent, so
                # "S&P 500" renders as typed, and build.py's own spoken-name table
                # already sends "The S&P 500" through it.
                if re.search(r"[<>]", v):
                    bad(f"market.json {slot}.{lg}: no markup — the speech bubble is "
                        f"plain text and would show the tag literally")
                if len(v) > cap:
                    bad(f"market.json {slot}.{lg}: {len(v)} chars, over the {cap} cap "
                        f"(it would overflow the bubble)")
        if not isinstance(d.get("lede"), list) or not d["lede"]:
            bad("market.json lede is missing or empty — the story must update with the numbers")
        if not isinstance(d.get("events"), list) or not d["events"]:
            bad("market.json events is missing or empty")
        for k in ("spx", "qqq", "nvda", "soxl", "cost"):
            pos = d.get("positions", {}).get(k, {})
            if not pos.get("price"):
                bad(f"market.json positions.{k} has no price")
            for f2 in ("news_en", "news_ko"):
                if not pos.get(f2):
                    bad(f"market.json positions.{k}.{f2} is missing or empty")
            if len(pos.get("news_en", [])) != len(pos.get("news_ko", [])):
                bad(f"market.json positions.{k}: news_en and news_ko have different lengths")
            if not pos.get("verdict_en") or not pos.get("verdict_ko"):
                bad(f"market.json positions.{k}: verdict missing in one language")
            if str(pos.get("drawdown", "")).strip() in ("-", "\u2014", "\u2013"):
                bad(f"market.json positions.{k}: drawdown is a bare dash — write a number "
                    f"(use '\u2248 0%' if there is no meaningful gap)")

print("  validation:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
PY
then
  fail "data validation"
fi

# --- 3. Build ----------------------------------------------------------------
echo
echo "--- 3/4  Building ---"
python3 scripts/build.py     || fail "build"
python3 scripts/sprite.py || fail "icon"
python3 scripts/wrap_site.py || fail "wrap"

# --- 4. Publish --------------------------------------------------------------
echo
echo "--- 4/4  Publishing ---"
# The project root is the repo now (site/ became docs/ when the whole project moved
# into it). The old check pointed at $ROOT/site, which no longer exists — so a run
# would rebuild locally and silently skip the push.
PUBLISHED=1
PUSHED=0

# The published URL, derived from the remote so a rename cannot leave this pointing at
# a site nobody updates any more.
site_url() {
  local u; u="$(git -C "$ROOT" remote get-url origin 2>/dev/null)" || return 1
  u="${u%.git}"
  local owner repo
  owner="$(basename "$(dirname "$u")")"; repo="$(basename "$u")"
  [ -n "$owner" ] && [ -n "$repo" ] || return 1
  printf 'https://%s.github.io/%s/' "$owner" "$repo"
}

# Did the reader actually get the new page? Not "did git push succeed" — on 2026-08-06
# the push succeeded at 04:35 and GitHub's own deploy queue stalled and timed out three
# times, so the page served Wednesday's brief until someone noticed by hand. Compare a
# hash of what we built against a hash of what the site is serving; a unique query
# string defeats the ten-minute CDN cache.
deployed() {
  local url want got
  url="$1"; want="$(shasum -a 256 < "$ROOT/docs/index.html" | cut -d' ' -f1)"
  got="$(curl -fsS --max-time 25 "${url}?v=$(date +%s)-$$" 2>/dev/null | shasum -a 256 | cut -d' ' -f1)"
  [ "$want" = "$got" ]
}

if git -C "$ROOT" remote get-url origin >/dev/null 2>&1; then
  git -C "$ROOT" add -A
  if git -C "$ROOT" diff --cached --quiet; then
    echo "  Nothing changed — not publishing."
  else
    git -C "$ROOT" -c user.name="market-recap-refresh" -c user.email="noreply@localhost" \
        commit -q -m "Refresh ($MODE) $(date '+%Y-%m-%d %H:%M')"
    if git -C "$ROOT" push -q origin main; then
      echo "  Pushed. Waiting for GitHub to actually serve it..."
      PUSHED=1
    else
      echo "  PUSH FAILED — the site still shows the previous page. Local files are current."
      PUBLISHED=0
    fi
  fi
else
  echo "  No git remote configured. Local files updated only."
fi

if [ "$PUSHED" = "1" ]; then
  URL="$(site_url)" || URL=""
  if [ -z "$URL" ]; then
    echo "  Could not derive the site URL — skipping the serve check."
  else
    PUBLISHED=0
    # Two windows with one nudge between them. A normal deploy lands inside the first.
    for attempt in 1 2; do
      for i in $(seq 1 18); do            # 18 x 20s = 6 minutes per window
        if deployed "$URL"; then
          echo "  Live and verified — the site is serving today's page."
          PUBLISHED=1
          break
        fi
        sleep 20
      done
      [ "$PUBLISHED" = "1" ] && break
      if [ "$attempt" = "1" ]; then
        # An empty commit is the one retrigger available without an API token, and it
        # is what cleared the stall by hand on 2026-08-06.
        echo "  Not serving yet after 6 minutes — nudging the deploy once."
        git -C "$ROOT" -c user.name="market-recap-refresh" -c user.email="noreply@localhost" \
            commit -q --allow-empty -m "Retrigger Pages deploy ($MODE)"
        git -C "$ROOT" push -q origin main || echo "  (nudge push failed)"
      fi
    done
    [ "$PUBLISHED" = "1" ] || echo "  STILL NOT SERVING after two attempts — GitHub Pages is not deploying."
  fi
fi

# The success stamp exists to stop the 6:57 and 7:42 backup slots re-running after a
# good morning. It means one thing only: THE READER CAN SEE TODAY'S PAGE. A run that
# built locally, or pushed to a repo GitHub then declined to deploy, has given him
# nothing — so it must not claim the day, and a later slot gets its turn. The work is
# already committed, so that slot republishes it along with whatever it finds.
if [ "$PUBLISHED" = "1" ]; then
  rm -f "$ROOT/.state/last-failure.txt"
  echo "$TODAY_STAMP" > "$STAMP"
else
  printf '%s  built but not serving — readers still see the previous page\n' \
    "$(date '+%Y-%m-%d %H:%M')" > "$ROOT/.state/last-failure.txt"
fi

echo
echo "Done — $(date '+%H:%M:%S')"
echo "Log: $LOG"

# Keep 60 days of logs.
find "$LOG_DIR" -name 'refresh-*.log' -mtime +60 -delete 2>/dev/null

exit 0
