#!/bin/bash
# Push whatever is committed, as soon as GitHub can actually build it.
# Pushing during an Actions outage triggers a publish run that dies at "Set up job"
# and emails a failure that means nothing. This waits instead.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$HOME/MarketRecap" || exit 1
. scripts/gh_healthy.sh
for i in $(seq 1 720); do            # up to 6 hours, checking every 30s
  if gh_actions_healthy; then
    if git push -q 2>/dev/null; then
      echo "$(date '+%Y-%m-%d %H:%M')  GitHub healthy again — pushed $(git rev-parse --short HEAD)"
    else
      echo "$(date '+%Y-%m-%d %H:%M')  push failed despite healthy status"
    fi
    exit 0
  fi
  sleep 30
done
echo "$(date '+%Y-%m-%d %H:%M')  gave up waiting after 6h — commits are local, push by hand"
