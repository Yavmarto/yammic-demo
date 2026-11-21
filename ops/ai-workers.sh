#!/usr/bin/env bash
# Print the PIDs of running AI extraction workers (`python -m app.ai`).
#
# One worker only: the service polls the queued runs, so a second worker races
# on the same run and double-posts proposals. `make demo` uses this list to
# detect a worker that a human already started by hand.
#
# Prints nothing when no worker runs. Exit code is 0 either way.
set -uo pipefail

ps -Ao pid=,command= | awk '
  /[Pp]ython.* -m app[.]ai( |$)/ && !/uv run/ && !/awk/ { print $1 }
'
