import os
import socket
from pathlib import Path

import pytest


def _docker_pg():
    try:
        socket.create_connection(("localhost", 5433), timeout=1).close()
        return "postgresql+psycopg://yammic:yammic@localhost:5433/yammic_test"
    except OSError:
        return None


def _make_url():
    if os.environ.get("TEST_DATABASE_URL"):
        return os.environ["TEST_DATABASE_URL"]
    import psycopg
    if url := _docker_pg():
        admin = "postgresql://yammic:yammic@localhost:5433/postgres"
    else:  # no Docker: embedded Postgres (pgserver dev dependency) on a unix socket
        import pgserver
        d = str(Path.home() / ".yammic-pg")
        pgserver.get_server(d, cleanup_mode=None)
        admin = f"postgresql://postgres:@/postgres?host={d}"
        url = f"postgresql+psycopg://postgres:@/yammic_test?host={d}"
    with psycopg.connect(admin, autocommit=True) as c:
        if not c.execute("SELECT 1 FROM pg_database WHERE datname='yammic_test'").fetchone():
            c.execute("CREATE DATABASE yammic_test")
    return url


os.environ["DATABASE_URL"] = _make_url()  # must be set before importing app.*

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app import seed  # noqa: E402
from app.db import engine, migrate  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    with engine.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE"))
        c.execute(text("CREATE SCHEMA public"))
    migrate()
    seed.load()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth(client):
    def _auth(user):
        t = client.post("/auth/login", json={"username": user, "password": "demo"}).json()["accessToken"]
        return {"Authorization": f"Bearer {t}"}
    return _auth
