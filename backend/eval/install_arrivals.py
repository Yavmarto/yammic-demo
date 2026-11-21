"""Insert the held-out "new arrivals" documents into the local demo database.

The real ingestion path is W3/W5 (FHIR pull). Until that lands, this helper
lets the AI workstream prove the live API flow on a brand-new participant
document set. It is a dev utility, not part of the API.

    cd backend
    uv run python -m eval.install_arrivals          # insert
    uv run python -m eval.install_arrivals --remove # delete
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from sqlalchemy import text

from app.db import engine

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "arrivals"


def _docs() -> list[dict]:
    index = json.loads((FIXTURES / "gold.json").read_text())
    out = []
    for d in index["documents"]:
        body = (FIXTURES / f"{d['id']}.txt").read_text()
        out.append({**d, "text": body, "sha256": hashlib.sha256(body.encode()).hexdigest()})
    return out


def install() -> None:
    with engine.begin() as c:
        for d in _docs():
            if not c.execute(text("SELECT 1 FROM participant WHERE id=:i"), {"i": d["participantId"]}).first():
                raise SystemExit(f"participant {d['participantId']} is not seeded")
            c.execute(text("""
                INSERT INTO source_document (id, participant_id, doc_type, title, language, document_date, text, sha256)
                VALUES (:id, :p, :t, :title, :lang, :date, :text, :sha)
                ON CONFLICT (id) DO UPDATE SET text=EXCLUDED.text, sha256=EXCLUDED.sha256,
                  title=EXCLUDED.title, doc_type=EXCLUDED.doc_type, document_date=EXCLUDED.document_date
            """), {"id": d["id"], "p": d["participantId"], "t": d["type"],
                   "title": d.get("title", d["id"]), "lang": d.get("language"),
                   "date": d.get("documentDate"), "text": d["text"], "sha": d["sha256"]})
    print(f"installed {len(_docs())} new-arrivals documents for "
          f"{sorted({d['participantId'] for d in _docs()})}")


def remove() -> None:
    with engine.begin() as c:
        ids = [d["id"] for d in _docs()]
        c.execute(text("DELETE FROM extraction WHERE document_id = ANY(:ids)"), {"ids": ids})
        c.execute(text("DELETE FROM source_document WHERE id = ANY(:ids)"), {"ids": ids})
    print(f"removed {len(ids)} new-arrivals documents")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--remove", action="store_true")
    args = ap.parse_args()
    if args.remove:
        remove()
    else:
        install()
    sys.exit(0)
