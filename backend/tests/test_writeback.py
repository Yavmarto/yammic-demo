import json
import sqlite3
from pathlib import Path

import pytest
from lxml import etree
from sqlalchemy import text

from app.db import engine
from app.writeback import LocalReceiver, TemporaryReceiverError, deliver


def test_local_writeback_retry_and_odm(client, auth, tmp_path):
    receiver = LocalReceiver(tmp_path / "receiver.sqlite")
    nurse = {"username": "nurse", "role": "nurse"}
    monitor = {"username": "monitor", "role": "monitor"}
    pid = "GBM-NL-001"
    proposals = client.get(f"/participants/{pid}/extractions", headers=auth("nurse")).json()
    kps = next(x for x in proposals if x["field"] == "KPS" and x["status"] == "proposed")
    assert deliver(pid, "KPS", monitor, receiver) is None
    with pytest.raises(PermissionError):
        deliver(pid, "KPS", nurse, receiver)
    # Defer first; only a reviewed accepted/corrected value may cross the boundary.
    assert client.post(f"/extractions/{kps['id']}/decision", json={"decision": "defer"}, headers=auth("nurse")).status_code == 200
    assert deliver(pid, "KPS", monitor, receiver) is None
    value = "80"
    assert client.post(f"/extractions/{kps['id']}/decision", json={"decision": "correct", "correctedValue": value, "reason": "Synthetic review"}, headers=auth("nurse")).status_code == 200
    with pytest.raises(TemporaryReceiverError):
        deliver(pid, "KPS", monitor, receiver, fail_after_commit=True)
    delivery = deliver(pid, "KPS", monitor, receiver)
    assert deliver(pid, "KPS", monitor, receiver) == delivery
    with sqlite3.connect(receiver.path) as db:
        rows = db.execute("SELECT delivery_id, payload FROM deliveries").fetchall()
    assert len(rows) == 1 and rows[0][0] == delivery
    payload = json.loads(rows[0][1])
    assert payload["value"] == value and payload["source_id"] == kps["documentId"]
    assert payload["evidence_link"] == f"/documents/{kps['documentId']}#extraction-{kps['id']}"
    assert payload["review_state"] == "corrected" and payload["destination_field"] == "performance.karnofsky"
    with pytest.raises(ValueError, match="Delivery identity conflict"):
        receiver.receive(delivery, {**payload, "value": "90"})
    with sqlite3.connect(receiver.path) as db:
        stored = db.execute("SELECT payload FROM deliveries WHERE delivery_id=?", (delivery,)).fetchone()
    assert json.loads(stored[0]) == payload
    with engine.connect() as c:
        actions = c.execute(text("SELECT action FROM audit_event WHERE entity_id=:i ORDER BY seq"), {"i": delivery}).scalars().all()
    assert actions == ["writeback.failed", "writeback.delivered", "writeback.delivered"]
    assert client.get("/audit/verify", headers=auth("monitor")).json()["ok"]
    response = client.get("/studies/GBM-NL-2026-01/export/odm", headers=auth("monitor"))
    assert response.status_code == 200
    doc = etree.fromstring(response.content)
    xsd = Path(__file__).resolve().parents[1] / "app/export/xsd/ODM1-3-2.xsd"
    etree.XMLSchema(etree.parse(str(xsd))).assertValid(doc)
    ns = {"o": "http://www.cdisc.org/ns/odm/v1.3"}
    assert doc.xpath("//o:ItemData[@Value='80']", namespaces=ns)
