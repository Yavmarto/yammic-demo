# Yammic demo backend (synthetic data only)

FastAPI + Postgres. Python 3.12, managed with uv.

```bash
cd backend
docker run -d --name yammic-pg -p 5433:5432 -e POSTGRES_USER=yammic -e POSTGRES_PASSWORD=yammic -e POSTGRES_DB=yammic postgres:16
#   no Docker?  export DATABASE_URL=$(uv run python -m app.devpg)
uv run python -m app.seed --reset      # migrate + load app/assets/data/*.json
uv run uvicorn app.main:app --port 8000
uv run pytest                          # uses localhost:5433/yammic_test, else embedded Postgres
uv run python -m app.export_openapi    # refresh openapi.json (a test fails if it is stale)
```

Swagger UI: http://localhost:8000/docs. Contract: `openapi.json`. Design: `../deliverables/backend_architecture.md`.
Demo users (password `demo`): `nurse`, `monitor`, `pi`; `ai` is the service role for the AI service.
Env: `DATABASE_URL` (default `postgresql+psycopg://yammic:yammic@localhost:5433/yammic`), `JWT_SECRET`.
