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
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +$STALE_AFTER 2>/dev/null)" ]; then
    echo "Clearing a stale lock (older than ${STALE_AFTER}m — previous run died without cleaning up)."
    rm -rf "$LOCK"
  fi
fi

if ! mkdir "$LOCK" 2>/dev/null; then
  echo "Another refresh is already running (lock: $LOCK). Exiting without changes."
  exit 0
fi
echo "$$" > "$LOCK/pid"
# rm -rf, not rmdir: the lock now holds a pid file, and rmdir would fail on a non-empty
# directory and leave the lock behind — reintroducing exactly the bug this guards against.
trap 'rm -rf "$LOCK" 2>/dev/null' EXIT INT TERM

# --- 0. Don't research a market that hasn't moved ------------------------------
# US market holidays land on weekdays; on those days there is no new close to report.
HOLIDAYS_2026="2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19 2026-07-03 2026-09-07 2026-11-26 2026-12-25"
TODAY="$(date +%Y-%m-%d)"
if [[ "$MODE" != "weekend" && "$HOLIDAYS_2026" == *"$TODAY"* ]]; then
  echo "Market holiday ($TODAY) — nothing new to report. Skipping."
  exit 0
fi

# --- 1. Research -------------------------------------------------------------
PROMPT_FILE="$ROOT/scripts/prompts/refresh-$MODE.md"
[ -f "$PROMPT_FILE" ] || fail "missing prompt file $PROMPT_FILE"

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

claude -p "$(cat "$PROMPT_FILE")" \
      --allowedTools WebSearch WebFetch Read "Edit(data/**)" \
      --add-dir "$ROOT/data" \
      --output-format text &
CPID=$!
( sleep "$RESEARCH_TIMEOUT"; kill -TERM "$CPID" 2>/dev/null ) &
WPID=$!
wait "$CPID"; RC=$?
kill "$WPID" 2>/dev/null; wait "$WPID" 2>/dev/null

if [ "$RC" -ne 0 ]; then
  [ "$RC" -ge 143 ] && echo "  (exit $RC — killed by the ${RESEARCH_TIMEOUT}s watchdog)"
  fail "research step (exit $RC)"
fi

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
echo
echo "--- 2/4  Validating data ---"
if ! python3 - <<'PY'
import json, re, sys, pathlib, datetime
root = pathlib.Path.cwd()
ok = True

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
        for k in ("spx", "qqq", "nvda", "soxl", "cost"):
            pos = d.get("positions", {}).get(k, {})
            if not pos.get("price"):
                bad(f"market.json positions.{k} has no price")
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
if git -C "$ROOT/site" remote get-url origin >/dev/null 2>&1; then
  bash scripts/deploy.sh || echo "  publish failed — local files are still updated"
else
  echo "  Not linked to GitHub Pages yet. Local files updated."
  echo "  Run ./scripts/deploy.sh once to create the public link."
fi

rm -f "$ROOT/.state/last-failure.txt"

echo
echo "Done — $(date '+%H:%M:%S')"
echo "Log: $LOG"

# Keep 60 days of logs.
find "$LOG_DIR" -name 'refresh-*.log' -mtime +60 -delete 2>/dev/null

exit 0
