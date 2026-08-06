#!/bin/bash
# Fetch quotes and publish them to the `live` branch FROM THIS MAC, with no GitHub
# Actions involved at all.
#
# The quote feed used to depend entirely on a workflow run. On 2026-08-06 GitHub Actions
# went into a major outage during market hours, so the workflow could not start, the feed
# froze, and the page correctly hid its prices — leaving the reader with no live numbers
# for hours over an outage that had nothing to do with the data.
#
# Nothing about fetching a quote needs a GitHub runner. `git push` works fine during an
# Actions outage (verified today), and the page reads live.json from
# raw.githubusercontent, which is a different service again. So when Actions is
# unavailable, the Mac simply does the job itself.
#
# Writes to the `live` orphan branch WITHOUT touching the working tree or the real index:
# the workflow's `git checkout --orphan` dance would wreck a live checkout that a refresh
# run may be using. Plumbing only.

set -uo pipefail
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

ROOT="$HOME/MarketRecap"
LOG="$ROOT/.state/logs/quotes-local.log"
mkdir -p "$(dirname "$LOG")"
say() { printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M')" "$1" >> "$LOG"; }

cd "$ROOT" || exit 1

# Market hours only (9:30–16:05 New York), weekdays.
H=$(TZ=America/New_York date +%H); M=$(TZ=America/New_York date +%M)
DOW=$(TZ=America/New_York date +%u)
[ "$DOW" -ge 6 ] && exit 0
NOW=$((10#$H * 60 + 10#$M))
{ [ "$NOW" -ge 570 ] && [ "$NOW" -le 965 ]; } || exit 0

python3 scripts/fetch_live.py >/dev/null 2>&1 || { say "fetch failed"; exit 1; }
[ -s live.json ] || { say "no live.json produced"; exit 1; }

# Build the commit with a throwaway index so the checkout is never disturbed.
TMPIDX="$(mktemp -t mmr-live-idx)"
export GIT_INDEX_FILE="$TMPIDX"
rm -f "$TMPIDX"
if ! git add -f live.json 2>/dev/null; then say "could not stage live.json"; rm -f "$TMPIDX"; exit 1; fi
TREE="$(git write-tree)" || { say "write-tree failed"; rm -f "$TMPIDX"; exit 1; }
COMMIT="$(git commit-tree "$TREE" -m "quotes $(date -u '+%H:%M UTC') (local)")" || {
  say "commit-tree failed"; rm -f "$TMPIDX"; exit 1; }
rm -f "$TMPIDX"
unset GIT_INDEX_FILE

if git push -q -f origin "$COMMIT:refs/heads/live" 2>/dev/null; then
  say "published quotes from this Mac (Actions not required)"
else
  say "push to live branch failed"
  exit 1
fi
