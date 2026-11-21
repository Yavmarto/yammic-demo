#!/usr/bin/env bash
# Health check for the local Yammic demo stack.
#
#   ops/health.sh            infrastructure must be up; app checks are reported as SKIP when down
#   ops/health.sh --strict   every component must be up (used by `make demo`)
#
# Exit codes: 0 all required checks pass, 1 otherwise.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

STRICT=0
case "${1:-}" in
  --strict|strict) STRICT=1 ;;
esac
[ "${STRICT:-0}" = "1" ] && STRICT=1

PG_PORT="${PG_PORT:-5433}"
FHIR_PORT="${FHIR_PORT:-8090}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
WEB_PORT="${WEB_PORT:-8080}"
FHIR_BASE="http://127.0.0.1:${FHIR_PORT}"
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

say "Yammic demo health — $(date '+%Y-%m-%d %H:%M:%S %Z')"
say ""

# ---------- Docker daemon ----------
if ! timeout 10 docker info >/dev/null 2>&1; then
  bad docker "Docker daemon is not reachable. Start Docker Desktop (see ops/RUNBOOK.md)."
else
  # ---------- PostgreSQL ----------
  if timeout 15 docker compose exec -T postgres pg_isready -U yammic -d yammic >/dev/null 2>&1; then
    version="$(timeout 15 docker compose exec -T postgres psql -U yammic -d yammic -tAc 'SHOW server_version' 2>/dev/null | tr -d '[:space:]')"
    ok postgres "127.0.0.1:${PG_PORT}  PostgreSQL ${version:-16}  db yammic"
    if ! timeout 15 docker compose exec -T postgres psql -U yammic -d hapi -tAc 'SELECT 1' >/dev/null 2>&1; then
      bad postgres "database 'hapi' is not reachable (HAPI FHIR schema not initialised yet?)"
    fi
  else
    bad postgres "127.0.0.1:${PG_PORT} not answering pg_isready (run: make up)"
  fi
fi

# ---------- HAPI FHIR ----------
if body="$(timeout 10 curl -fsS --max-time 8 "${FHIR_BASE}/fhir/metadata" 2>/dev/null)"; then
  if [[ "$body" == *'"resourceType"'*'"CapabilityStatement"'* ]]; then
    ok fhir "${FHIR_BASE}/fhir/metadata  CapabilityStatement R4"
  else
    bad fhir "${FHIR_BASE}/fhir/metadata answered but is not a FHIR CapabilityStatement"
  fi
else
  if timeout 10 docker compose ps --status running --services 2>/dev/null | grep -qx hapi; then
    warn fhir "${FHIR_BASE}/fhir/metadata not answering yet (HAPI first boot takes 60-180 s)"
  else
    bad fhir "${FHIR_BASE}/fhir/metadata not reachable (run: make up)"
  fi
fi

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
    say "Result: OK — full demo stack is healthy."
  else
    say "Result: OK — infrastructure healthy$([ "$SKIP" -ne 0 ] && echo " (${SKIP} app component(s) not started; use 'make demo')")."
  fi
  exit 0
fi
say "Result: FAIL — ${FAIL} check(s) failed. See ops/RUNBOOK.md."
exit 1
