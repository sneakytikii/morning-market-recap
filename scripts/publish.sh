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

echo "==> 1/2  Pushing the project"
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
echo "==> 2/2  Pointing GitHub Pages at docs/"
gh api -X PUT "repos/$REPO/pages" -f "source[branch]=main" -f "source[path]=/docs" >/dev/null 2>&1 \
  && echo "    Pages now serves docs/" \
  || echo "    (could not change it automatically — see the manual step below)"


echo
echo "-----------------------------------------------------------"
echo "Done. Your link (unchanged):"
echo "   https://sneakytikii.github.io/morning-market-recap/"
echo
echo "The local Mac schedule is untouched and still running — the Mac"
echo "wakes at 06:05 Mon-Fri and refreshes at 06:12."
echo "-----------------------------------------------------------"
