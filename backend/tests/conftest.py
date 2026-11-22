import os
import socket
from pathlib import Path

import pytest


def _docker_pg():
    for port in (5434, 5433):
        try:
            socket.create_connection(("localhost", port), timeout=1).close()
            return port, f"postgresql+psycopg://yamicc:yamicc@localhost:{port}/yamicc_v4_test"
        except OSError:
            continue
    return None


def _make_url():
    if os.environ.get("TEST_DATABASE_URL"):
        return os.environ["TEST_DATABASE_URL"]
    import psycopg
    if pg := _docker_pg():
        port, url = pg
        admin = f"postgresql://yamicc:yamicc@localhost:{port}/postgres"
    else:  # no Docker: embedded Postgres (pgserver dev dependency) on a unix socket
        import pgserver
        d = str(Path.home() / ".yamicc-pg")
        pgserver.get_server(d, cleanup_mode=None)
        admin = f"postgresql://postgres:@/postgres?host={d}"
        url = f"postgresql+psycopg://postgres:@/yamicc_v4_test?host={d}"
    with psycopg.connect(admin, autocommit=True) as c:
        if not c.execute("SELECT 1 FROM pg_database WHERE datname='yamicc_v4_test'").fetchone():
            c.execute("CREATE DATABASE yamicc_v4_test")
    return url


import tempfile  # noqa: E402

os.environ.update(JWT_SECRET="test-jwt-secret-" + "x" * 32, PSEUDONYM_KEY="test-pseudonym-key-" + "x" * 32,
                  AUDIT_KEY="test-audit-key-" + "x" * 32,
                  AUDIT_ANCHOR=os.path.join(tempfile.mkdtemp(), "audit-anchor.log"))
os.environ["DATABASE_URL"] = _make_url()  # must be set before importing app.*

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app import seed  # noqa: E402
from app.db import engine, migrate  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    open(os.environ["AUDIT_ANCHOR"], "w").close()  # new DB, new anchor
    with engine.connect() as lock_conn:
        lock_conn.execute(text("SELECT pg_advisory_lock(7740)"))
        lock_conn.commit()
        try:
            with engine.begin() as c:
                c.execute(text("DROP SCHEMA public CASCADE"))
                c.execute(text("CREATE SCHEMA public"))
            migrate()
            site = os.environ.get("TEST_SITE_ID")
            original_j = seed.J
            if site:
                parts = original_j("participants.json")
                parts["participants"] = [p for p in parts["participants"] if p["siteId"] == site]
                ids = {p["id"] for p in parts["participants"]}
                docs = original_j("documents.json")
                docs["documents"] = [d for d in docs["documents"] if d["participantId"] in ids]
                doc_ids = {d["id"] for d in docs["documents"]}
                ex = original_j("extractions.json")
                ex["extractions"] = [e for e in ex["extractions"] if e["documentId"] in doc_ids]
                study = original_j("study.json")
                study["sites"] = [s for s in study["sites"] if s["id"] == site]
                selected = {"participants.json": parts, "documents.json": docs, "extractions.json": ex, "study.json": study}
                seed.J = lambda name: selected[name] if name in selected else original_j(name)
            try:
                seed.load()
            finally:
                seed.J = original_j
            yield
        finally:
            lock_conn.execute(text("SELECT pg_advisory_unlock(7740)"))
            lock_conn.commit()


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
