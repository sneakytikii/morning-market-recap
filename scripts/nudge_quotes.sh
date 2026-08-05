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
gh workflow run "Live quotes" -R sneakytikii/morning-market-recap >/dev/null 2>&1
