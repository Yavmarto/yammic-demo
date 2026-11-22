# Yamicc demo backend (synthetic data only)

FastAPI + Postgres. Python 3.12, managed with uv.

```bash
cd backend
docker run -d --name yamicc-pg -p 5433:5432 -e POSTGRES_USER=yamicc -e POSTGRES_PASSWORD=yamicc -e POSTGRES_DB=yamicc postgres:16
#   no Docker?  export DATABASE_URL=$(uv run python -m app.devpg)
uv run python -m app.seed --reset      # migrate + load app/assets/data/*.json
uv run uvicorn app.main:app --port 8000
uv run pytest                          # uses localhost:5433/yamicc_test, else embedded Postgres
uv run python -m app.export_openapi    # refresh openapi.json (a test fails if it is stale)
```

Swagger UI: http://localhost:8000/docs. Contract: `openapi.json`. Design: `../deliverables/backend_architecture.md`.
Demo users (password `demo`): `nurse`, `monitor`, `pi`; `ai` is the service role for the AI service.
Env: `DATABASE_URL` (default `postgresql+psycopg://yamicc:yamicc@localhost:5433/yamicc`), `JWT_SECRET`.

### Local synthetic write-back

The receiver is disabled unless `YAMICC_SYNTHETIC_WRITEBACK=1` and
`YAMICC_SYNTHETIC_RECEIVER_PATH` names a local SQLite file. Enable both only
for a separate synthetic backend with a dedicated synthetic database, bound to
loopback and a spare port. For example, after configuring the usual database and
secrets for that isolated runtime:

```sh
YAMICC_SYNTHETIC_WRITEBACK=1 \
YAMICC_SYNTHETIC_RECEIVER_PATH="$PWD/synthetic-receiver.sqlite" \
uv run uvicorn app.main:app --host 127.0.0.1 --port 8013
```

The Flutter export page reviews and sends the corrected or accepted KPS for
fictional participant GBM-NL-001. PI and monitor are the existing demo export
roles; this restriction does not decide FR-063. A retry uses the reviewed
identity, and the receiver retains one record. ODM remains available. This is
local synthetic feasibility only; it is not an EDC integration.
