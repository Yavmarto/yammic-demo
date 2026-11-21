#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
bin="${CHROME:-$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1194/chrome-mac/headless_shell}"
if [[ ! -x "$bin" ]]; then
  echo "headless shell not found: $bin" >&2
  echo "set CHROME=/path/to/headless_shell" >&2
  exit 1
fi
mkdir -p "$here/shots"
names=(01_screening 02_site_comparison 03_queries_sdv 04_participant_timeline 05_protocol_form 06_states)
for i in "${!names[@]}"; do
  n=$((i + 1))
  "$bin" --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --window-size=1440,900 --virtual-time-budget=1500 \
    --screenshot="$here/shots/${names[$i]}.png" \
    "file://$here/index.html?only=$n" >/dev/null 2>&1
  echo "wrote shots/${names[$i]}.png"
done
