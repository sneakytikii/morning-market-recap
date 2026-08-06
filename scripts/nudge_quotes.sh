#!/bin/bash
# Fallback trigger for the live-quotes workflow. GitHub's own cron is the primary; this
# nudges the same workflow from the Mac every 15 minutes during market hours in case
# GitHub's scheduler lags (observed: a newly added cron that had not engaged an hour in).
# The workflow's concurrency group dedupes if both fire. Outside market hours: no-op.
export PATH="$HOME/.local/bin:/usr/bin:/bin"
H=$(TZ=America/New_York date +%H); M=$(TZ=America/New_York date +%M); DOW=$(TZ=America/New_York date +%u)
[ "$DOW" -ge 6 ] && exit 0
NOW=$((10#$H * 60 + 10#$M))
{ [ "$NOW" -ge 570 ] && [ "$NOW" -le 965 ]; } || exit 0   # 9:30–16:05 ET

# When GitHub Actions is healthy, let the runner do it — that path keeps working when
# this Mac is asleep, which is most of why it exists.
#
# When Actions is down, do NOT dispatch: during the 2026-08-06 outage this fired every
# 15 minutes and produced a failed run and an email each time. Fetch the quotes here
# instead. Nothing about reading a price needs a GitHub runner, `git push` keeps working
# through an Actions outage, and the page reads the feed from raw.githubusercontent,
# which is a different service again — so the reader keeps his live prices.
. "$(dirname "$0")/gh_healthy.sh"
if gh_actions_healthy; then
  gh workflow run "Live quotes" -R sneakytikii/morning-market-recap >/dev/null 2>&1
else
  exec bash "$(dirname "$0")/push_quotes_local.sh"
fi
