#!/usr/bin/env bash
# Create ops/.env.local (git-ignored) with per-machine random secrets on first run. Never overwrites.
# One file per checkout: the v3 stack (~/yammic-demo-v3 or ~/yammic-demo) and the v4 stack
# (~/yammic-v4) each keep their own secrets, so neither can log in to the other's database.
set -euo pipefail
f="$(dirname "$0")/.env.local"
[ -f "$f" ] && exit 0
r() { openssl rand -hex 24; }
umask 077
cat > "$f" <<EOT
# Generated $(date +%F) by ops/ensure-env.sh. Local only, not committed. Delete to regenerate (then: make reset).
JWT_SECRET=$(r)
PSEUDONYM_KEY=$(r)
AUDIT_KEY=$(r)
APP_DB_PASSWORD=$(r)
HAPI_DB_PASSWORD=$(r)
HAPI2_DB_PASSWORD=$(r)
EOT
echo "== generated $f" >&2
