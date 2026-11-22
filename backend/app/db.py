import os
from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://yamicc:yamicc@127.0.0.1:5435/yamicc")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


def migrate(eng=None):
    """Apply migrations/*.sql in name order, once each."""
    eng = eng or engine
    with eng.begin() as c:
        c.execute(text("CREATE TABLE IF NOT EXISTS schema_migration (name text PRIMARY KEY)"))
        done = {r[0] for r in c.execute(text("SELECT name FROM schema_migration"))}
        for f in sorted(MIGRATIONS.glob("*.sql")):
            if f.name not in done:
                c.exec_driver_sql(f.read_text().replace("%", "%%"))
                c.execute(text("INSERT INTO schema_migration VALUES (:n)"), {"n": f.name})


if __name__ == "__main__":
    migrate()
    print("migrated")
