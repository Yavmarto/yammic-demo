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
            db.execute(
                "INSERT INTO deliveries (delivery_id, payload) VALUES (?, ?) "
                "ON CONFLICT (delivery_id) DO NOTHING",
                (delivery_id, serialized),
            )
            stored_payload, = db.execute(
                "SELECT payload FROM deliveries WHERE delivery_id=?", (delivery_id,)
            ).fetchone()
            if stored_payload != serialized:
                raise ValueError("Delivery identity conflict")
        if fail_after_commit:
            raise TemporaryReceiverError("Simulated lost acknowledgement after receiver commit")


def prepare(participant_id, field_id, receiver):
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
    return delivery_id, payload


def deliver(participant_id, field_id, user, receiver, *, fail_after_commit=False, expected_id=None):
    # Demo export roles only; FR-063 remains open.
    if user.get("role") not in ("pi", "monitor"):
        raise PermissionError("Write-back requires pi or monitor")
    prepared = prepare(participant_id, field_id, receiver)
    if prepared is None:
        return None
    delivery_id, payload = prepared
    if expected_id is not None and delivery_id != expected_id:
        raise ValueError("Reviewed value changed; review it again")
    destination = payload["destination_field"]
    row = {"document_id": payload["source_id"]}
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
