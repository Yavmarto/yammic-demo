#!/usr/bin/env bash
# Print the PIDs of running AI extraction workers that talk to THIS stack's
# backend. Two things keep v4 and the frozen v3 stack apart:
#   - the API URL filter: v3's worker has no --api flag (it defaults to :8000),
#     v4's worker is started with `--api http://127.0.0.1:8001`;
#   - `make` starts v4's worker through the service entry point
#     (`python -c 'from app.ai.service import main'`), not `-m app.ai`, so v3's
#     older ai-workers.sh (which matches `-m app.ai`) does not see it either.
#
# One worker per stack: the service polls the queued runs, so a second worker
# races on the same run and double-posts proposals. `make demo` uses this list to
# detect a worker that a human already started by hand.
#
# Override the filter with AI_API_URL (default: YAMICC_API_URL, else v4 :8001).
# Prints nothing when no matching worker runs. Exit code is 0 either way.
set -uo pipefail

api="${AI_API_URL:-${YAMICC_API_URL:-http://127.0.0.1:8001}}"

# -ww: do not truncate the command line to the terminal width (the URL is at the end).
ps -ww -Ao pid=,command= | awk -v api="$api" '
  /[Pp]ython/ && /app[.]ai/ && !/uv run/ && !/awk/ { if (index($0, api)) print $1 }
'
