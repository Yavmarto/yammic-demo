"""Local feasibility adapter. No external trial system is contacted."""
import hashlib
import json
import sqlite3
from urllib.parse import quote

from sqlalchemy import text

from . import audit
from .db import engine


class TemporaryReceiverError(Exception):
    pass


class LocalReceiver:
    # This mapping is owned by the simulated receiver, not by the source eCRF.
    fields = {"KPS": "performance.karnofsky"}

    def __init__(self, path):
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS deliveries (
                delivery_id TEXT PRIMARY KEY, payload TEXT NOT NULL)""")

    def receive(self, delivery_id, payload, *, fail_after_commit=False):
        if payload["destination_field"] not in self.fields.values():
            raise ValueError("Receiver does not support destination field")
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with sqlite3.connect(self.path) as db:
            existing = db.execute("SELECT payload FROM deliveries WHERE delivery_id=?", (delivery_id,)).fetchone()
            if existing and existing[0] != serialized:
                raise ValueError("Delivery identity conflict")
            db.execute("INSERT OR IGNORE INTO deliveries VALUES (?, ?)", (delivery_id, serialized))
        if fail_after_commit:
            raise TemporaryReceiverError("Simulated lost acknowledgement after receiver commit")


def deliver(participant_id, field_id, user, receiver, *, fail_after_commit=False):
    # Same export roles as the existing FHIR push, not a new authorization policy.
    if user.get("role") not in ("pi", "monitor"):
        raise PermissionError("Write-back requires pi or monitor")
    destination = receiver.fields.get(field_id)
    if destination is None:
        raise ValueError("No receiver mapping for field")
    with engine.connect() as c:
        row = c.execute(text("""SELECT v.value, v.verified_at, e.id extraction_id, e.document_id,
              e.review_state, p.study_id, p.site_id
            FROM ecrf_value v JOIN extraction e ON e.id=v.source_extraction_id
            JOIN participant p ON p.id=v.participant_id
            WHERE v.participant_id=:p AND v.field_id=:f
              AND e.review_state IN ('accepted','corrected')"""),
            {"p": participant_id, "f": field_id}).mappings().first()
    if not row:
        return None
    payload = {"study": row["study_id"], "site": row["site_id"], "subject": participant_id,
               "destination_field": destination, "value": row["value"],
               "source_id": row["document_id"], "extraction_id": row["extraction_id"],
               "evidence_link": "/documents/" + quote(row["document_id"], safe="") + "#extraction-" + quote(row["extraction_id"], safe=""),
               "review_state": row["review_state"]}
    identity = json.dumps([participant_id, field_id, row["extraction_id"], row["verified_at"].isoformat()], separators=(",", ":"))
    delivery_id = hashlib.sha256(identity.encode()).hexdigest()
    try:
        receiver.receive(delivery_id, payload, fail_after_commit=fail_after_commit)
    except TemporaryReceiverError:
        with engine.begin() as c:
            audit.record(c, user, "writeback.failed", "delivery", delivery_id, participant_id=participant_id,
                         after={"reason": "temporary receiver failure", "retryable": True})
        raise
    with engine.begin() as c:
        audit.record(c, user, "writeback.delivered", "delivery", delivery_id, participant_id=participant_id,
                     after={"sourceId": row["document_id"], "destinationField": destination})
    return delivery_id
