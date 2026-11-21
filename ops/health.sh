#!/usr/bin/env bash
# Health check for the local Yamicc v4 demo stack (parallel with the frozen v3 stack).
#
#   ops/health.sh            infrastructure must be up; app checks are reported as SKIP when down
#   ops/health.sh --strict   every component must be up, including the AI worker and both hospitals
#
# Ports come from the environment and default to the v4 values:
#   Postgres 5434, hospital 1 8091, hospital 2 8092, backend 8001, web 8081.
# Exit codes: 0 all required checks pass, 1 otherwise.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
[ -f ops/.env.local ] && { set -a; . ops/.env.local; set +a; }  # compose needs the DB passwords

STRICT=0
case "${1:-}" in
  --strict|strict) STRICT=1 ;;
esac
[ "${STRICT:-0}" = "1" ] && STRICT=1

PG_PORT="${PG_PORT:-5434}"
FHIR_PORT="${FHIR_PORT:-8091}"
FHIR2_PORT="${FHIR2_PORT:-8092}"
BACKEND_PORT="${BACKEND_PORT:-8001}"
WEB_PORT="${WEB_PORT:-8081}"
FHIR_BASE="http://127.0.0.1:${FHIR_PORT}"
FHIR2_BASE="http://127.0.0.1:${FHIR2_PORT}"
BACKEND_BASE="http://127.0.0.1:${BACKEND_PORT}"
WEB_BASE="http://127.0.0.1:${WEB_PORT}"

FAIL=0
SKIP=0
BACKEND_STATE="down"
WEB_STATE="down"

say() { printf '%s\n' "$*"; }
ok()   { printf '[ OK ] %-10s %s\n' "$1" "$2"; }
warn() { printf '[WARN] %-10s %s\n' "$1" "$2"; }
skip() { printf '[SKIP] %-10s %s\n' "$1" "$2"; SKIP=$((SKIP + 1)); }
bad()  { printf '[FAIL] %-10s %s\n' "$1" "$2"; FAIL=$((FAIL + 1)); }

fhir_metadata() { # $1 = base URL, $2 = label, $3 = compose service name
  local base="$1" label="$2" service="$3" body
  if body="$(timeout 10 curl -fsS --max-time 8 "${base}/fhir/metadata" 2>/dev/null)"; then
    if [[ "$body" == *'"resourceType"'*'"CapabilityStatement"'* ]]; then
      ok "$label" "${base}/fhir/metadata  CapabilityStatement R4"
    else
      bad "$label" "${base}/fhir/metadata answered but is not a FHIR CapabilityStatement"
    fi
  else
    if timeout 10 docker compose ps --status running --services 2>/dev/null | grep -qx "$service"; then
      warn "$label" "${base}/fhir/metadata not answering yet (HAPI first boot takes 60-180 s)"
    else
      bad "$label" "${base}/fhir/metadata not reachable (run: make up)"
    fi
  fi
}

say "Yamicc v4 demo health — $(date '+%Y-%m-%d %H:%M:%S %Z')"
say ""

# ---------- Docker daemon ----------
if ! timeout 10 docker info >/dev/null 2>&1; then
  bad docker "Docker daemon is not reachable. Start Docker Desktop (see ops/RUNBOOK.md)."
else
  # ---------- PostgreSQL (backend db + both HAPI dbs) ----------
  if timeout 15 docker compose exec -T postgres pg_isready -U yamicc -d yamicc >/dev/null 2>&1; then
    version="$(timeout 15 docker compose exec -T postgres psql -U yamicc -d yamicc -tAc 'SHOW server_version' 2>/dev/null | tr -d '[:space:]')"
    ok postgres "127.0.0.1:${PG_PORT}  PostgreSQL ${version:-16}  db yamicc"
    if ! timeout 15 docker compose exec -T postgres psql -U yamicc -d hapi -tAc 'SELECT 1' >/dev/null 2>&1; then
      bad postgres "database 'hapi' (hospital 1) is not reachable (HAPI schema not initialised yet?)"
    fi
    if ! timeout 15 docker compose exec -T postgres psql -U yamicc -d hapi2 -tAc 'SELECT 1' >/dev/null 2>&1; then
      bad postgres "database 'hapi2' (hospital 2) is not reachable (HAPI schema not initialised yet?)"
    fi
  else
    bad postgres "127.0.0.1:${PG_PORT} not answering pg_isready (run: make up)"
  fi
fi

# ---------- HAPI FHIR, both hospitals ----------
fhir_metadata "$FHIR_BASE" "fhir-h1" hapi
fhir_metadata "$FHIR2_BASE" "fhir-h2" hapi2

# ---------- Backend (outside Docker) ----------
if body="$(timeout 8 curl -fsS --max-time 5 "${BACKEND_BASE}/health" 2>/dev/null)"; then
  BACKEND_STATE="up"
  if [[ "$body" == *'"status"'*'"ok"'* ]]; then
    ok backend "${BACKEND_BASE}/health  ${body}"
  else
    warn backend "${BACKEND_BASE}/health degraded: ${body}"
    [ "$STRICT" = "1" ] && FAIL=$((FAIL + 1))
  fi
else
  skip backend "${BACKEND_BASE}/health not running (start: make backend, or make demo)"
fi

# ---------- AI extraction worker (outside Docker, this stack only) ----------
ai_pids="$(YAMICC_API_URL="$BACKEND_BASE" ops/ai-workers.sh 2>/dev/null | tr '\n' ' ' | sed 's/ $//')"
if [ -n "$ai_pids" ]; then
  ai_n="$(printf '%s\n' "$ai_pids" | wc -w | tr -d '[:space:]')"
  if [ "$ai_n" -gt 1 ]; then
    bad ai "pid ${ai_pids} — ${ai_n} workers run; one worker only (make stop, then make demo)"
  else
    ok ai "pid ${ai_pids}  consumes queued extraction runs  log: ops/logs/ai.log"
  fi
elif [ "$BACKEND_STATE" = "down" ]; then
  skip ai "AI worker not started (start: make demo, or make ai)"
elif [ "$STRICT" = "1" ]; then
  bad ai "no AI worker for ${BACKEND_BASE} — queued runs stay queued and live extraction times out (start: make demo)"
else
  skip ai "no AI worker — queued runs will not be consumed (start: make ai, or make demo)"
fi

# ---------- Flutter web ----------
if body="$(timeout 8 curl -fsS --max-time 5 "${WEB_BASE}/" 2>/dev/null)"; then
  WEB_STATE="up"
  shopt -s nocasematch
  if [[ "$body" == *'<html'* ]]; then
    ok web "${WEB_BASE}/  serving Flutter web build"
  else
    warn web "${WEB_BASE}/ answered but does not look like the Flutter web build"
    [ "$STRICT" = "1" ] && FAIL=$((FAIL + 1))
  fi
else
  skip web "${WEB_BASE}/ not served (build + serve: make web, or make demo)"
fi

say ""
if [ "$FAIL" -eq 0 ]; then
  if [ "$STRICT" = "1" ]; then
    if [ "$SKIP" -ne 0 ]; then
      say "Result: FAIL — strict mode but ${SKIP} component(s) not running."
      exit 1
    fi
    say "Result: OK — full v4 demo stack is healthy (both hospitals)."
  else
    say "Result: OK — infrastructure healthy$([ "$SKIP" -ne 0 ] && echo " (${SKIP} app component(s) not started; use 'make demo')")."
  fi
  exit 0
fi
say "Result: FAIL — ${FAIL} check(s) failed. See ops/RUNBOOK.md."
exit 1
