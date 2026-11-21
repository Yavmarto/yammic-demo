#!/usr/bin/env bash
# Create ops/.env.local (git-ignored) with per-machine random secrets on first run. Never overwrites.
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
EOT
echo "== generated $f" >&2
