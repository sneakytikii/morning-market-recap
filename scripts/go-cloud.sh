#!/bin/bash
# Move the scheduled refresh off this Mac and onto GitHub's servers.
#
#   ./scripts/go-cloud.sh
#
# Does three things:
#   1. pushes the whole project to the repo (it currently holds only the built page)
#   2. repoints GitHub Pages at docs/
#   3. turns off the local launchd jobs, so the two schedules cannot both run
#
# After this the site updates whether or not this Mac is awake, on, or in the room.

set -uo pipefail
export PATH="$HOME/.local/bin:$HOME/.nvm/versions/node/v24.18.0/bin:$PATH"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
REPO="sneakytikii/morning-market-recap"

echo "==> 1/3  Pushing the project"
# Commit anything the last local refresh left behind, or the newest numbers stay on this
# Mac while the site shows the older ones.
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "    committing pending local changes first"
  git add -A
  git -c user.name="${GIT_NAME:-Daniel Kim}" -c user.email="${GIT_EMAIL:-danielkimmy0704@gmail.com}" \
      commit -q -m "Latest local refresh"
fi
git push --force -u origin main || { echo "push failed"; exit 1; }

echo
echo "==> 2/3  Pointing GitHub Pages at docs/"
gh api -X PUT "repos/$REPO/pages" -f "source[branch]=main" -f "source[path]=/docs" >/dev/null 2>&1 \
  && echo "    Pages now serves docs/" \
  || echo "    (could not change it automatically — see the manual step below)"

echo
echo "==> 3/3  Turning off the local Mac schedule"
for m in weekday tracker weekend; do
  P="$HOME/Library/LaunchAgents/com.danielkim.marketrecap.$m.plist"
  [ -f "$P" ] && launchctl unload "$P" 2>/dev/null && echo "    stopped: $m"
done
echo "    (the plists are kept — re-enable with launchctl load if you ever want them back)"

echo
echo "-----------------------------------------------------------"
echo "One thing left, and it has to be done in a browser:"
echo
echo "  Add your Anthropic API key so the cloud job can do the research."
echo
echo "  1. Get a key:  https://console.anthropic.com/settings/keys"
echo "  2. Add it here: https://github.com/$REPO/settings/secrets/actions/new"
echo "       Name:   ANTHROPIC_API_KEY"
echo "       Secret: (paste the key)"
echo
echo "  Then test it immediately, without waiting for tomorrow:"
echo "     https://github.com/$REPO/actions  ->  'Refresh the dashboard'"
echo "     -> 'Run workflow' -> mode: weekday -> Run"
echo
echo "  Your link stays the same:"
echo "     https://sneakytikii.github.io/morning-market-recap/"
echo "-----------------------------------------------------------"
