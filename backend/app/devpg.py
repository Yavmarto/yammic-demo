"""No Docker? Start an embedded Postgres (dev dependency `pgserver`) and print its DATABASE_URL.

    export DATABASE_URL=$(uv run python -m app.devpg)
"""
from pathlib import Path

import pgserver
import psycopg

d = str(Path.home() / ".yammic-pg")
pgserver.get_server(d, cleanup_mode=None)
with psycopg.connect(f"postgresql://postgres:@/postgres?host={d}", autocommit=True) as c:
    if not c.execute("SELECT 1 FROM pg_database WHERE datname='yammic'").fetchone():
        c.execute("CREATE DATABASE yammic")
print(f"postgresql+psycopg://postgres:@/yammic?host={d}")
