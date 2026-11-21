# Yammic demo — local platform runbook

Owner: DevOps (CEL-1773). Scope: the local demo stack for Monday 2026-11-23.
Everything runs on this machine. **Synthetic data only. No hosting, no outreach, no paid APIs (Gate 3).**

## 1. What runs where

| Component | Where | Address | Started by |
|---|---|---|---|
| PostgreSQL 16 | Docker `yammic-postgres` | `127.0.0.1:5433` · db `yammic` and `hapi` · user/pass `yammic`/`yammic` | `make up` / `make reset` / `make demo` |
| HAPI FHIR JPA server (R4) | Docker `yammic-hapi` | `http://127.0.0.1:8090/fhir` | `make up` / `make reset` / `make demo` |
| FastAPI backend | host process via `uv` | `http://127.0.0.1:8000` · `/health`, `/docs` | `make backend` (foreground) or `make demo` (background) |
| Flutter web app | host process, `python3 -m http.server` | `http://127.0.0.1:8080` | `make web` (foreground) or `make demo` (background) |

Data volume: Docker named volume `yammic-postgres-data`. It holds both the backend data and the HAPI schema.
FHIR data is stored in PostgreSQL database `hapi`, created by `ops/postgres-init.sql` on first boot.

Ports are bound to `127.0.0.1` on purpose. Other machines cannot reach them. QA runs on this machine.

## 2. Prerequisites

- Docker Desktop installed and running (`docker info` succeeds).
- `uv` on `PATH` (`uv --version`).
- Flutter SDK at `~/flutter/bin/flutter`, or set `FLUTTER=/path/to/flutter`.
- `curl` and `python3`.
- `timeout` (GNU coreutils; Homebrew `coreutils`). Used by `make health` and the start-up waits.
- Images already pulled (they are pinned by digest in `docker-compose.yml`):
  - `postgres:16@sha256:3950ad7c…`
  - `hapiproject/hapi:latest@sha256:0ff86aac…`

The demo does not pull images. If the local image store is wiped, run
`docker compose pull` once with network access.

## 3. Cold start (first time on a machine, or after a reset)

```bash
cd ~/yammic-demo
make reset          # remove volumes, start Postgres + HAPI, wait healthy, seed
make demo           # start backend + web in the background, health-check everything
open http://127.0.0.1:8080
```

`make reset` alone brings up the infrastructure and data. `make demo` adds the backend and web app.

## 4. Daily / demo start

```bash
make demo           # idempotent: reuses running services, seeds only when empty
make health         # infrastructure checks
make health STRICT=1   # all four components must be up
```

Expected `make demo` output ends with `Result: OK — full demo stack is healthy.`

## 5. Stop and clean

| Command | Effect |
|---|---|
| `make stop` | Stop backend/web processes and containers. Data is kept. |
| `make down` | Stop containers only. Data is kept. |
| `make reset` | **Delete all data** (`down -v`), start fresh, seed. |

Logs: `ops/logs/backend.log`, `ops/logs/web.log`, `ops/logs/web-build.log`.
PIDs: `ops/run/backend.pid`, `ops/run/web.pid`.

## 6. Recovery

### 6.1 Docker daemon is not running

Symptom: `make up` prints `ERROR: Docker daemon not reachable`, or `docker info` hangs/fails.

1. Start Docker Desktop from the Dock or with `open -a Docker`.
2. Wait until `docker info` succeeds (first start after boot can take 1–3 minutes).
3. Retry `make up`.

If Docker Desktop is running but its engine stays `stopped` (`docker desktop status`), restart it:

```bash
docker desktop stop
open -a Docker
```

**If Docker Desktop was started from an agent/SSH shell and dies with
`opening tray: starting electron: unmarshaling start request: unexpected EOF`**, the inherited
shell environment breaks its helper processes. Start the backend headless with a clean
environment instead (no tray UI, but `docker compose` works):

```bash
pkill -f com.docker.backend
env -i HOME="$HOME" USER="$USER" PATH="/usr/bin:/bin:/usr/sbin:/sbin" TMPDIR=/tmp \
  nohup /Applications/Docker.app/Contents/MacOS/com.docker.backend \
  -unattended -with-frontend=false > /tmp/docker-headless.log 2>&1 &
# wait ~30-60 s, then:
docker desktop status     # Status: running
docker info
```

On a normal desktop session this is not needed; use the Docker Desktop app.

### 6.2 A port is already taken

Symptom: `Bind for 127.0.0.1:5433 failed: port is already allocated` or `make health` shows a foreign service.

```bash
lsof -nP -iTCP:5433 -sTCP:LISTEN    # Postgres
lsof -nP -iTCP:8090 -sTCP:LISTEN    # HAPI
lsof -nP -iTCP:8000 -sTCP:LISTEN    # backend
lsof -nP -iTCP:8080 -sTCP:LISTEN    # web
```

Stop the other process (another agent's stack, a previous demo, a native Postgres).
Then `make stop && make demo`.

### 6.3 HAPI is slow to start

First boot creates the whole HAPI schema in PostgreSQL and takes **60–180 s**. Normal.
`make up` waits (up to 420 s). Watch progress:

```bash
docker compose logs -f hapi | grep -iE "Started|ERROR|Exception"
curl -fsS http://127.0.0.1:8090/fhir/metadata | head -c 200
```

If it is still not healthy after 4 minutes:

```bash
docker compose ps            # hapi should be "starting" or "unhealthy"
docker compose logs --tail=200 hapi
```

Common causes: PostgreSQL not ready (check `docker compose logs postgres`), port conflict, or
insufficient memory (Docker Desktop needs ~8 GB; the stack requests 1.5 GB for HAPI).

### 6.4 Reset the database

```bash
make reset
```

This removes `yammic-postgres-data`, recreates it, and re-seeds. Use it when data is inconsistent,
after a schema change, or before a demo. It deletes all local demo data; that is expected.

Nuclear option (also clears images/containers for this project):

```bash
docker compose down -v --remove-orphans
docker volume rm yammic-postgres-data 2>/dev/null || true
make reset
```

### 6.5 Backend cannot reach PostgreSQL

Symptom: `make health` shows `backend ... degraded`, or `backend.log` has `connection refused`.

- Default DSN: `postgresql+psycopg://yammic:yammic@localhost:5433/yammic`.
- Check: `docker compose exec postgres pg_isready -U yammic -d yammic`.
- If you changed the host port, export `DATABASE_URL` before `make backend`.
- `make up` must be running first.

### 6.6 Seed skipped or failed

`make seed` skips a component when its script is not present yet (workstream not landed). This is normal
during the build-up to the demo. A failed FHIR seed usually means HAPI is not healthy yet:
wait, then `make seed`.

The backend seed is skipped when the `study` table already has rows. Use `make reset` for a clean slate.

### 6.7 Flutter web build fails

```bash
cat ops/logs/web-build.log
```

Then build by hand to see the error:

```bash
cd app && ~/flutter/bin/flutter pub get && ~/flutter/bin/flutter build web --release
```

`make demo` rebuilds the web app only when `app/lib`, `app/web`, `app/assets` or `app/pubspec.yaml`
are newer than `app/build/web/index.html`.

## 7. Pre-demo checklist (T-15 minutes)

- [ ] Docker Desktop is running: `docker info` prints a server version.
- [ ] `make reset && make demo` completes, final line `Result: OK — full demo stack is healthy.`
- [ ] `curl -fsS http://127.0.0.1:8090/fhir/metadata` returns a `CapabilityStatement`.
- [ ] `curl -fsS http://127.0.0.1:8000/health` returns `{"status":"ok",...}`.
- [ ] `open http://127.0.0.1:8080` shows the login screen; log in with a demo role.
- [ ] Browser zoom is 100%, screen mirroring is correct.
- [ ] `ops/logs/` has no growing error tail: `tail -n 50 ops/logs/*.log`.
- [ ] Backend-down fallback: stop the backend (`make stop` is too broad) — the app must show the
      read-only offline snapshot. Restart with `make demo`.
- [ ] Laptop is on power, sleep is disabled, no OS update pending.
- [ ] No real patient data on screen or in the dataset.

## 8. Notes and boundaries

- No production systems, no cloud resources, no paid APIs. `claude` AI provider stays off (Gate 3).
- HAPI FHIR uses the local PostgreSQL database `hapi`. Do not point it at a real FHIR endpoint.
- Do not change `docker-compose.yml` ports or volume names without telling the other workstreams:
  W3 (FHIR seed) expects `:8090`, W1/W5 expect Postgres on `:5433`.
