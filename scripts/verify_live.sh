#!/bin/bash
# Does the live site actually serve the page we built? If not, re-trigger the publish.
#
# Why this exists: on 2026-08-06 the morning run researched, built and pushed Thursday's
# brief at 04:35, and GitHub's deploy backend then stalled and timed out repeatedly. The
# push had succeeded, so nothing on our side thought anything was wrong, and the reader
# was served Wednesday's page for four hours until a human happened to look.
#
# The morning run now verifies its own publish, but that only covers the minutes right
# after it runs. This closes the rest of the day: a small, cheap check that keeps asking
# the only question that matters — can he see today's page? — and quietly fixes it when
# GitHub recovers from whatever was wrong.
#
# Deliberately does NOT build, research, or edit anything. It re-triggers a deploy of
# what is already committed, or it does nothing.

set -uo pipefail
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

ROOT="$HOME/MarketRecap"
LOG="$ROOT/.state/logs/verify-live.log"
mkdir -p "$(dirname "$LOG")"

say() { printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M')" "$1" >> "$LOG"; }

cd "$ROOT" 2>/dev/null || { say "cannot cd to $ROOT"; exit 0; }
[ -f docs/index.html ] || { say "no docs/index.html — nothing to check"; exit 0; }

# Never fight a run in progress: it is mid-publish and owns this question.
if [ -d "$ROOT/.state/refresh.lock" ]; then
  P="$(cat "$ROOT/.state/refresh.lock/pid" 2>/dev/null)"
  if [ -n "$P" ] && kill -0 "$P" 2>/dev/null; then exit 0; fi
fi

# Only judge what has actually been pushed. A locally-edited or unpushed docs/index.html
# SHOULD differ from the live site, and triggering a deploy for it would publish work in
# progress — the opposite of helpful.
git diff --quiet -- docs/ 2>/dev/null || exit 0
git diff --cached --quiet -- docs/ 2>/dev/null || exit 0
LOCAL="$(git rev-parse HEAD 2>/dev/null)"
REMOTE="$(git ls-remote origin main 2>/dev/null | cut -f1)"
[ -n "$LOCAL" ] && [ -n "$REMOTE" ] && [ "$LOCAL" = "$REMOTE" ] || exit 0

URL="https://sneakytikii.github.io/morning-market-recap/"
WANT="$(shasum -a 256 < docs/index.html | cut -d' ' -f1)"
GOT="$(curl -fsS --max-time 25 "${URL}?v=$(date +%s)-$$" 2>/dev/null | shasum -a 256 | cut -d' ' -f1)"

[ -z "$GOT" ] && exit 0                      # no network here: not GitHub's problem
[ "$WANT" = "$GOT" ] && exit 0               # all well, say nothing

say "site is NOT serving the current build"

# Wait out a known outage rather than adding to it. A dispatch during the 2026-08-06
# Actions outage died at "Set up job" every time and sent an email for each attempt;
# it published nothing and told nobody anything true. The check fails open, so an
# unreachable status API still lets us try.
. "$(dirname "$0")/gh_healthy.sh"
if ! gh_actions_healthy; then
  say "  GitHub reports an Actions/Pages outage — holding off, will retry next tick"
  exit 0
fi

# One run at a time. Dispatching while a run is already queued or in flight does not
# speed anything up: under the workflow's "pages" concurrency group the new dispatch
# replaces the previously queued run, so a 20-minute cadence against anything that
# waits longer than 20 minutes means no run ever survives to completion. That exact
# loop ate 2026-08-06 through 08-08 — one run wedged in "waiting" held the group for
# two days while every fresh dispatch cancelled the previous pending one. So: leave a
# young run alone, cancel a genuinely stuck one, and only dispatch into a clear queue.
STUCK_AFTER=1800   # seconds; a healthy publish completes in under a minute
NOW="$(date +%s)"
OPEN="$(gh api "repos/sneakytikii/morning-market-recap/actions/workflows/pages.yml/runs?per_page=20" \
        --jq '.workflow_runs[] | select(.status != "completed") | "\(.id) \(.created_at)"' 2>/dev/null)"
DISPATCH=yes
while read -r RID CREATED _; do
  [ -n "${RID:-}" ] || continue
  T="$(date -j -u -f "%Y-%m-%dT%H:%M:%SZ" "${CREATED:-}" +%s 2>/dev/null || echo 0)"
  AGE=$(( NOW - T ))
  if [ "$T" -gt 0 ] && [ "$AGE" -lt "$STUCK_AFTER" ]; then
    say "  a publish run ($RID) is already ${AGE}s in — leaving it to finish"
    DISPATCH=no
  else
    say "  cancelling publish run $RID, stuck for ${AGE}s"
    gh run cancel "$RID" -R sneakytikii/morning-market-recap >/dev/null 2>&1
  fi
done <<< "$OPEN"

if [ "$DISPATCH" = yes ]; then
  if gh workflow run "Publish the page" -R sneakytikii/morning-market-recap >/dev/null 2>&1; then
    say "  re-triggered the publish workflow"
  else
    say "  dispatch failed — will try again next tick"
  fi
fi
