#!/bin/bash
# Is GitHub Actions actually able to run a job right now?
#
# Sourced by anything that dispatches a workflow. On 2026-08-06 GitHub had an Actions
# outage — jobs died at "Set up job" with "Failed to resolve action download info:
# Service Unavailable", before a single line of our code ran. Every 15-minute quote
# nudge and every publish attempt during that window produced a failed run and an email,
# none of which meant anything about this project.
#
# Firing work into a service that is known to be down does not make it arrive sooner. It
# just manufactures alarm. Ask first; when GitHub says it is broken, wait quietly and try
# on the next tick.
#
# Fails OPEN: if the status API is unreachable or its shape changes, we assume healthy
# and dispatch as before. Missing status information must never become a reason to stop
# publishing.

gh_actions_healthy() {
  local json
  json="$(curl -fsS --max-time 10 https://www.githubstatus.com/api/v2/summary.json 2>/dev/null)" || return 0
  printf '%s' "$json" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)                      # unparseable: fail open
# "degraded_performance" belongs on this list, learned the hard way: while GitHub was
# reporting merely degraded on 2026-08-06, runs were still dying at "Set up job" and
# emailing a failure each time. Waiting one more 15- or 20-minute tick costs nothing —
# the watchdog retries and the page already hides stale prices rather than lying — so
# treat anything short of operational as "come back later".
BAD = ("degraded_performance", "partial_outage", "major_outage")
for c in d.get("components", []):
    if c.get("name") in ("Actions", "Pages") and c.get("status") in BAD:
        sys.exit(1)
sys.exit(0)
' 2>/dev/null
}
