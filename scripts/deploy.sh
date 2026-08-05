#!/bin/bash
# Publish the dashboard to GitHub Pages — a plain https:// link anyone can open.
#
# Run once to create the site. After that, the morning refresh calls this automatically
# and the link updates itself; nobody has to re-send anything.
#
#   ./scripts/deploy.sh
#
# Creating the repo is a publish-to-the-internet action, so the first run needs your
# explicit go-ahead. Everything the page shows is public market data — five ticker
# symbols and commentary. It contains no name, no holdings, no dollar amounts, and no
# share counts (verified by scan).

set -euo pipefail

export PATH="$HOME/.local/bin:$HOME/.nvm/versions/node/v24.18.0/bin:$PATH"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="morning-market-recap"
cd "$ROOT"

echo "==> Rebuilding site files"
python3 scripts/build.py      # data + template -> dashboard.html (idempotent)
python3 scripts/sprite.py
python3 scripts/wrap_site.py

cd "$ROOT"

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "==> First run: creating the public repo and turning on GitHub Pages"
  git add -A
  git -c user.name="${GIT_NAME:-Market Recap}" -c user.email="${GIT_EMAIL:-noreply@localhost}" \
      commit -q -m "Morning Market Recap" || true
  git branch -M main
  gh repo create "$REPO" --public --source=. --remote=origin --push \
     --description "Plain-English morning market recap — five positions, English/Korean"

  OWNER="$(gh api user --jq .login)"
  # Serve the repo root on main.
  gh api -X POST "repos/$OWNER/$REPO/pages" \
     -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 \
   || gh api -X PUT "repos/$OWNER/$REPO/pages" \
     -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 \
   || echo "    (Pages may already be enabled — continuing)"

  echo
  echo "    Your link:  https://$OWNER.github.io/$REPO/"
  echo "    First build takes about a minute. After that it is instant."
else
  echo "==> Publishing update"
  git add -A
  if git diff --cached --quiet; then
    echo "    No changes to publish."
  else
    git -c user.name="${GIT_NAME:-Market Recap}" -c user.email="${GIT_EMAIL:-noreply@localhost}" \
        commit -q -m "Recap update $(date '+%Y-%m-%d %H:%M')"
    git push -q origin main
    OWNER="$(gh api user --jq .login)"
    echo "    Published — https://$OWNER.github.io/$REPO/"
  fi
fi
