"""Gold labels for the eval harness.

The synthetic generator's records in ``app/assets/data/extractions.json`` are the
gold source. Two adjustments are required:

* the seeded "wrong value" demo case is *not* gold: its ``seededIssue`` states
  the expected correct value (``unmethylated``), and that is what the harness
  scores against;
* abstentions stay abstentions (``PROGDAT`` has no RANO assessment).

The held-out ``fixtures/arrivals`` set is a small, hand-written "new arrivals"
document set used for the live demo and for a generalisation check.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
DATA = ROOT / "app" / "assets" / "data"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fields() -> list[dict[str, Any]]:
    return json.loads((DATA / "study.json").read_text())["ecrf"]["fields"]


def load_documents() -> list[dict[str, Any]]:
    index = json.loads((DATA / "documents.json").read_text())["documents"]
    docs = []
    for d in index:
        docs.append({
            "id": d["id"],
            "participantId": d["participantId"],
            "type": d["type"],
            "title": d["title"],
            "language": d.get("language"),
            "documentDate": d.get("documentDate"),
            "text": (DATA / "documents" / f"{d['id']}.txt").read_text(),
        })
    return docs


def load_gold() -> dict[str, dict[str, dict[str, Any]]]:
    """Return ``{documentId: {field: {status, value, normalizedValue, ...}}}``."""
    data = json.loads((DATA / "extractions.json").read_text())
    gold: dict[str, dict[str, dict[str, Any]]] = {}
    for r in data["extractions"]:
        field = r["field"]
        doc = r["documentId"]
        bucket = gold.setdefault(doc, {})
        if field in bucket:  # the fixture has one duplicate SUBJID record
            continue
        status = r["status"]
        value = r.get("value")
        normalized = r.get("normalizedValue")
        issue = r.get("seededIssue") or {}
        if issue.get("kind") == "wrong_value":
            value = issue.get("expectedCorrectValue", value)
            normalized = issue.get("expectedCorrectValue", normalized)
        bucket[field] = {
            "status": "abstained" if status == "abstained" else "proposed",
            "value": None if status == "abstained" else value,
            "normalizedValue": None if status == "abstained" else normalized,
            "fieldLabel": r.get("fieldLabel"),
            "seededIssue": issue or None,
        }
    return gold


def seeded_cases() -> dict[str, Any]:
    return json.loads((DATA / "extractions.json").read_text())["seededDemoCases"]


def load_arrivals() -> tuple[list[dict[str, Any]], dict[str, dict[str, dict[str, Any]]]]:
    index = json.loads((FIXTURES / "arrivals" / "gold.json").read_text())
    docs = []
    gold: dict[str, dict[str, dict[str, Any]]] = {}
    for d in index["documents"]:
        docs.append({
            "id": d["id"], "participantId": d["participantId"], "type": d["type"],
            "title": d.get("title", d["id"]), "language": d.get("language"),
            "documentDate": d.get("documentDate"),
            "text": (FIXTURES / "arrivals" / f"{d['id']}.txt").read_text(),
        })
        gold[d["id"]] = d["fields"]
    return docs, gold


def load_set(name: str = "all") -> tuple[list[dict[str, Any]], dict[str, dict[str, dict[str, Any]]], dict[str, Any]]:
    """Load ``gold``, ``arrivals`` or ``all`` documents and their labels."""
    if name in ("gold", "all"):
        docs = load_documents()
        gold = load_gold()
        meta = {"name": "generator-gold", "documents": len(docs), "hardCases": seeded_cases()}
        if name == "gold":
            return docs, gold, meta
    if name in ("arrivals", "all"):
        adocs, agold = load_arrivals()
        meta = {"name": "arrivals-heldout", "documents": len(adocs),
                "hardCases": {k: v for k, v in seeded_cases().items() if k == "abstention"}}
        if name == "arrivals":
            return adocs, agold, meta
    assert name == "all"
    docs = load_documents() + adocs
    gold = {**load_gold(), **agold}
    return docs, gold, {"name": "all", "documents": len(docs),
                        "hardCases": seeded_cases(), "arrivals": len(adocs)}
