# Yammic demo — local platform runbook (v4)

Owner: DevOps (CEL-1801). Scope: the local v4 demo stack for Monday 2026-11-23.
Everything runs on this machine. **Synthetic data only. No hosting, no outreach, no paid APIs (Gate 3).**

The frozen v3 checkpoint runs next to v4 on this machine. The two stacks have their own
compose project, volume, ports, secrets file and processes. Starting, stopping or resetting
v4 must never touch v3.

## 1. What runs where — v3 and v4 side by side

| Component | v3 (frozen checkpoint) | v4 (this checkout) |
|---|---|---|
| Worktree | `~/yammic-demo-v3` | `~/yammic-v4` (branch `v4`) |
| Compose project | `yammic-demo` | `yammic-v4` |
| PostgreSQL 16 | `127.0.0.1:5433` · db `yammic`, `hapi` | `127.0.0.1:5434` · db `yammic`, `hapi`, `hapi2` |
| Hospital 1 FHIR (HAPI R4) | `http://127.0.0.1:8090/fhir` | `http://127.0.0.1:8091/fhir` · db `hapi` |
| Hospital 2 FHIR (HAPI R4) | — | `http://127.0.0.1:8092/fhir` · db `hapi2` |
| FastAPI backend | `http://127.0.0.1:8000` | `http://127.0.0.1:8001` |
| AI extraction worker | polls `:8000` | polls `:8001` (`--api`), one per stack |
| Flutter web app | `http://127.0.0.1:8080` | `http://127.0.0.1:8081` |
| Data volume | `yammic-postgres-data` | `yammic-v4-postgres-data` |
| Container names | fixed (`yammic-postgres`, `yammic-hapi`) | auto (`yammic-v4-postgres-1`, `yammic-v4-hapi-1`, `yammic-v4-hapi2-1`) |

Ports are bound to `127.0.0.1` on purpose. Other machines cannot reach them.

v4 services (compose file `docker-compose.yml`):

| Service | Image | Host port | Database | DB role |
|---|---|---|---|---|
| `postgres` | `postgres:16` (pinned digest) | `PG_PORT` (5434) | `yammic` | owner `yammic`; app `yammic_app` |
| `hapi` | `hapiproject/hapi` (pinned digest) | `FHIR_PORT` (8091) | `hapi` | `hapi` |
| `hapi2` | `hapiproject/hapi` (same digest) | `FHIR2_PORT` (8092) | `hapi2` | `hapi2` |

All ports come from the environment. The defaults are the v4 values above; override with
`PG_PORT`, `FHIR_PORT`, `FHIR2_PORT`, `BACKEND_PORT`, `WEB_PORT` if needed.

## 2. Prerequisites

- Docker Desktop installed and running (`docker info` succeeds). The v4 stack runs two HAPI
  JVMs (1.5 GB heap each) next to v3's; about 8 GB of Docker memory is comfortable.
- `uv` on `PATH` (`uv --version`).
- Flutter SDK at `~/flutter/bin/flutter`, or set `FLUTTER=/path/to/flutter`.
- `curl`, `python3`, and GNU `timeout` (Homebrew `coreutils`). Used by `make health` and the waits.
- Images already pulled (pinned by digest in `docker-compose.yml`):
  `postgres:16@sha256:3950ad7c…` and `hapiproject/hapi:latest@sha256:0ff86aac…`.
  The demo does not pull images. If the local image store is wiped, run `docker compose pull`
  once with network access.

## 3. Cold start (v4)

```bash
cd ~/yammic-v4
make reset          # remove the v4 volume, start Postgres + both HAPI servers, seed
make demo           # start backend :8001 + one AI worker + web :8081, health-check all
open http://127.0.0.1:8081
```

`make reset` only affects compose project `yammic-v4`. The v3 stack on 5433/8090/8000/8080
keeps running.

`make seed` loads hospital 1 with
`fhir-seed/load.py --hospital 1 --set baseline --base-url http://127.0.0.1:8091/fhir` and hospital 2
with `--hospital 2 --set baseline --base-url http://127.0.0.1:8092/fhir`. Hospital 2 is skipped
when `fhir-seed/hospital2/<set>/manifest.json` is absent; the target prints
`skip FHIR hospital 2 — no <dir> data yet`.

Seed sets per hospital (override from the environment):

| Variable | Default | Data | Use |
|---|---|---|---|
| `FHIR_H1_SET` | `baseline` | `fhir-seed/baseline/` | hospital 1 baseline bundles |
| `FHIR_H1_ARRIVALS` | `arrivals` | `fhir-seed/arrivals/` | hospital 1 live-sync arrivals |
| `FHIR_H2_SET` | `baseline` | `fhir-seed/hospital2/baseline/` | hospital 2 baseline bundles |
| `FHIR_H2_ARRIVALS` | `arrivals` | `fhir-seed/hospital2/arrivals/` | hospital 2 live-sync arrivals |

## 4. Backend settings for the two hospitals

`make` exports these to the backend (and to every child process):

| Variable | Value |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://yammic_app:<secret>@127.0.0.1:5434/yammic` |
| `FHIR_BASE_URL` | `http://127.0.0.1:8091/fhir` (hospital 1; backward-compatible single source) |
| `FHIR_SOURCES` | JSON array: `[{"id":"hospital-1","name":"Hospital 1","url":"http://127.0.0.1:8091/fhir"},{"id":"hospital-2","name":"Hospital 2","url":"http://127.0.0.1:8092/fhir"}]` |
| `YAMMIC_API_URL` | `http://127.0.0.1:8001` (the AI worker uses this backend, never v3's :8000) |

`FHIR_SOURCES` is the multi-site contract for the backend (task D): one object per hospital with
`id`, display `name` and FHIR base `url`. It is a JSON array on a single line.
W1/W5 still read `FHIR_BASE_URL`; it points at hospital 1.

## 5. Daily / demo start and checks

```bash
make demo              # idempotent: reuses running services, seeds only when empty
make health            # infrastructure checks
make health STRICT=1   # all components must be up: both hospitals, backend, AI worker, web
```

Expected `make demo` ends with `Result: OK — full v4 demo stack is healthy (both hospitals).`
and a line `AI worker: <pid> — consumes queued extraction runs (one worker per stack)`.

`make health` checks:

- Postgres on 5434, and that databases `hapi` and `hapi2` are reachable.
- Hospital 1 `:8091/fhir/metadata` and hospital 2 `:8092/fhir/metadata` return a CapabilityStatement.
- Backend `:8001/health`, the v4 AI worker (port-scoped), and web `:8081`.

`make stage-arrivals` loads the live-sync arrivals into both hospitals (hospital 2 only when its
data set exists), without changing the platform data. Use it to make the pre-demo state one command:
`make reset && make stage-arrivals && make demo`.

## 6. Stop and clean

| Command (run in `~/yammic-v4`) | Effect |
|---|---|
| `make stop` | Stop this stack's backend, AI worker and web, then the v4 containers. Data is kept. |
| `make down` | Stop v4 containers only. Data is kept. |
| `make reset` | **Delete v4 data** (`down -v`), start fresh, seed. v3 is not touched. |

Logs: `ops/logs/backend.log`, `ops/logs/ai.log`, `ops/logs/web.log`, `ops/logs/web-build.log`.
PIDs: `ops/run/backend.pid`, `ops/run/ai.pid`, `ops/run/web.pid`.

The v4 `ops/ai-workers.sh` only reports workers whose command line contains this stack's API URL
(`--api http://127.0.0.1:8001`), so `make stop` and `make demo` do not stop or reuse v3's worker.
The reverse is not true: v3's older `ops/ai-workers.sh` matches every `python -m app.ai` process.
**While a v4 worker runs, do not run v3's `make stop` (it kills both) or v3's `make demo` (it may
reuse the v4 worker).** Stop v4 first: `cd ~/yammic-v4 && make stop`.

## 7. Recovery

### 7.1 Docker daemon is not running

Symptom: `make up` prints `ERROR: Docker daemon not reachable`, or `docker info` hangs/fails.

1. Start Docker Desktop from the Dock or with `open -a Docker`.
2. Wait until `docker info` succeeds (first start after boot can take 1–3 minutes).
3. Retry `make up`.

If Docker Desktop is running but its engine stays `stopped` (`docker desktop status`), restart it:

```bash
docker desktop stop
open -a Docker
```

If Docker Desktop was started from an agent/SSH shell and dies with
`opening tray: starting electron: unmarshaling start request: unexpected EOF`, start the backend
headless with a clean environment (no tray UI, but `docker compose` works):

```bash
pkill -f com.docker.backend
env -i HOME="$HOME" USER="$USER" PATH="/usr/bin:/bin:/usr/sbin:/sbin" TMPDIR=/tmp \
  nohup /Applications/Docker.app/Contents/MacOS/com.docker.backend \
  -unattended -with-frontend=false > /tmp/docker-headless.log 2>&1 &
# wait ~30-60 s, then:
docker desktop status     # Status: running
docker info
```

### 7.2 A port is already taken

Symptom: `Bind for 127.0.0.1:5434 failed: port is already allocated`, or `make health` shows a
foreign service. Check the v4 ports first; a hit on the v3 ports belongs to the frozen stack and
must stay.

```bash
lsof -nP -iTCP:5434 -sTCP:LISTEN    # v4 Postgres
lsof -nP -iTCP:8091 -sTCP:LISTEN    # v4 hospital 1
lsof -nP -iTCP:8092 -sTCP:LISTEN    # v4 hospital 2
lsof -nP -iTCP:8001 -sTCP:LISTEN    # v4 backend
lsof -nP -iTCP:8081 -sTCP:LISTEN    # v4 web
# v3, do not touch: 5433, 8090, 8000, 8080
```

Stop the foreign process, or set another free port in the environment, then `make stop && make demo`.

### 7.3 HAPI is slow to start (either hospital)

First boot creates the whole HAPI schema in PostgreSQL and takes **60–180 s per server**. Normal.
`make up` waits up to 600 s. Watch progress:

```bash
docker compose logs -f hapi  | grep -iE "Started|ERROR|Exception"   # hospital 1
docker compose logs -f hapi2 | grep -iE "Started|ERROR|Exception"   # hospital 2
curl -fsS http://127.0.0.1:8091/fhir/metadata | head -c 200
curl -fsS http://127.0.0.1:8092/fhir/metadata | head -c 200
```

If a server is still not healthy after 4 minutes:

```bash
docker compose ps            # hapi / hapi2 should be "starting" or "unhealthy"
docker compose logs --tail=200 hapi2
```

Common causes: PostgreSQL not ready (`docker compose logs postgres`), port conflict, or insufficient
Docker memory (two HAPI JVMs at 1.5 GB each).

### 7.4 Reset the v4 database

```bash
make reset
```

This removes `yammic-v4-postgres-data`, recreates it, and re-seeds **only the v4 stack**. Use it when
v4 data is inconsistent, after a schema change, or before a demo.

Nuclear option for v4 only:

```bash
docker compose down -v --remove-orphans
docker volume rm yammic-v4-postgres-data 2>/dev/null || true
make reset
```

Never run `docker compose down -v` in `~/yammic-demo-v3`.

### 7.5 Backend cannot reach PostgreSQL

Symptom: `make health` shows `backend ... degraded`, or `backend.log` has `connection refused`.

- The Makefile exports `DATABASE_URL` on port **5434**. The code default is still 5433 (v3);
  always start the backend through `make backend` or `make demo` so it gets the v4 URL.
- Check: `docker compose exec postgres pg_isready -U yammic -d yammic`.
- If you changed the host port, export `DATABASE_URL` before `make backend`.
- `make up` must be running first.

### 7.6 Seed skipped or failed

`make seed` skips a component when its script or data is not present yet. This is normal during the
build-up to the demo:

- hospital 1: fails if `fhir-seed/baseline/manifest.json` is missing (that data is committed).
- hospital 2: skipped until `fhir-seed/hospital2/<set>/manifest.json` exists (task C adds it).
- backend: skipped when the `study` table already has rows. Use `make reset` for a clean slate.

A failed FHIR seed usually means HAPI is not healthy yet: wait, then `make seed`.

### 7.7 Flutter web build fails

```bash
cat ops/logs/web-build.log
```

Then build by hand to see the error:

```bash
cd app && ~/flutter/bin/flutter pub get && ~/flutter/bin/flutter build web --release
```

`make demo` rebuilds the web app only when `app/lib`, `app/web`, `app/assets` or `app/pubspec.yaml`
are newer than `app/build/web/index.html`.

### 7.8 Live extraction times out, or runs stay `queued`

Symptom: **Run extraction** spins for 90 s and then says "Is the AI service running?".
`make health` shows `ai ... no AI worker`, or the run never leaves `queued`.

The AI extraction worker is a separate process, scoped to this stack's API:

```bash
ops/ai-workers.sh                 # v4 worker PID(s); nothing when none run
tail -n 50 ops/logs/ai.log        # one JSON line per run: ai.run_start, ai.run, ai.poll_error
```

Restart it with `make demo` (background) or `make ai` (foreground, for debugging).
`make ai` refuses to start when a v4 worker already runs.

**One worker per stack.** A second worker can pick the same run and post duplicate proposals.
`make demo` reuses a running v4 worker; it never starts a second one.

The worker logs in as the `ai` service user through the REST API and holds no database credentials.
A worker that cannot log in exits at once with a traceback in `ops/logs/ai.log`; `make demo` reports
`AI worker exited during startup` and stops.

## 8. Pre-demo checklist (T-15 minutes)

- [ ] Docker Desktop is running: `docker info` prints a server version.
- [ ] `docker ps` shows both stacks: v3 (`yammic-postgres`, `yammic-hapi`) and v4
      (`yammic-v4-postgres-1`, `yammic-v4-hapi-1`, `yammic-v4-hapi2-1`), all healthy.
- [ ] `make reset && make demo` completes in `~/yammic-v4`, final line
      `Result: OK — full v4 demo stack is healthy (both hospitals).`
- [ ] `ops/ai-workers.sh` prints exactly one PID, and `make demo` shows the AI worker line.
- [ ] `tail -n 20 ops/logs/ai.log` has no `ai.poll_error` or `ai.run_error` lines.
- [ ] Both FHIR servers answer: `curl -fsS http://127.0.0.1:8091/fhir/metadata` and `:8092`.
- [ ] `curl -fsS http://127.0.0.1:8001/health` returns `{"status":"ok",...}`.
- [ ] `open http://127.0.0.1:8081` shows the login screen; log in with a demo role.
- [ ] `tail -n 50 ops/logs/*.log` shows no growing error tail.
- [ ] v3 is still healthy if it is the fallback (`curl :8090/fhir/metadata`, `:8000/health`, `:8080`).
- [ ] Browser zoom is 100%, screen mirroring is correct, laptop on power, sleep disabled.
- [ ] No real patient data on screen or in the dataset.

## 9. Notes and boundaries

- No production systems, no cloud resources, no paid APIs. The `claude` AI provider stays off (Gate 3).
- Run **one** AI worker per stack. The v4 worker is scoped to `:8001`.
- Do not change v4 ports, project name or volume names without telling the other workstreams:
  task C (FHIR seed, hospital 2), task D (backend, `FHIR_SOURCES`) and task F (web) depend on them.
- Do not stop, restart or reset the v3 stack. If a v4 change would touch it, flag it to the CTO first.

## 10. Secrets, DB roles and known risks

- **Secrets.** The first `make` run writes `ops/.env.local` (git-ignored, mode 600) with random
  `JWT_SECRET`, `PSEUDONYM_KEY`, `AUDIT_KEY`, `APP_DB_PASSWORD`, `HAPI_DB_PASSWORD` and
  `HAPI2_DB_PASSWORD`. The backend refuses to start without them (no committed default). The file is
  per checkout: v4's secrets cannot open v3's database. Deleting it means a new `make reset`.
- **DB roles** (made by `ops/postgres-init.sh`, only on a fresh v4 volume):
  `yammic` = owner/superuser for migrations and seed; `yammic_app` = the running backend;
  `hapi` = hospital 1, can only connect to database `hapi`; `hapi2` = hospital 2, only `hapi2`.
- **Audit chain.** Hashes are HMAC-SHA256 with `AUDIT_KEY`. Each committed write appends
  `time count headHash` to `ops/audit-anchor.log`. `/audit/verify` fails on edits, mid-chain
  deletion, tail deletion and a full rewrite. `make reset` deletes only v4's anchor with the DB.
- **Known risk: HAPI image.** `hapiproject/hapi:latest` (pinned digest, HAPI 8.12.0) carries
  Spring/OTel CVEs (4 Critical, 25 High at scan). Local demo mitigation: both ports bound to
  127.0.0.1 only, each HAPI has its own low-privilege DB user, CORS pinned to `http://127.0.0.1:8081`.
  Re-check upstream before any use outside a local demo. HAPI has no authentication and serves raw
  synthetic MRN and names.
