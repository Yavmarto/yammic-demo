#!/usr/bin/env python3
"""Validate the synthetic demo dataset.

Checks, independently of the generator:
  * every evidence span is inside the document text and matches exactly
  * the embedded sourceText equals the .txt file byte-for-byte
  * document checksums and lengths in documents.json are correct
  * referential integrity between participants, documents, extractions, eCRF
  * the three deliberate demo cases exist and are coherent

Exit code 0 = pass, 1 = validation errors.

Run:  python3 app/tool/validate_data.py
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys

APP = pathlib.Path(__file__).resolve().parents[1]
DATA = APP / "assets" / "data"

PARTICIPANT_STATUSES = {"screening", "enrolled", "active", "completed", "withdrawn"}
ECRF_STATUSES = {"not_started", "in_progress", "complete", "awaiting_review"}
VISIT_STATUSES = {"completed", "scheduled", "missed"}
EXTRACTION_STATUSES = {"proposed", "abstained"}

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def load(name: str) -> dict:
    path = DATA / name
    if not path.exists():
        fail(f"missing file: {path}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{name}: invalid JSON: {exc}")
        return {}


def check_banner(doc_id: str, text: str) -> None:
    head = text[:200].upper()
    if "SYNTHETI" not in head or "FICT" not in head:
        fail(f"{doc_id}: missing synthetic/fictional banner in the first 200 chars")


def main() -> int:
    study = load("study.json")
    participants_doc = load("participants.json")
    documents_doc = load("documents.json")
    extractions_doc = load("extractions.json")
    dashboard = load("dashboard.json")

    for name, doc in (
        ("study.json", study),
        ("participants.json", participants_doc),
        ("documents.json", documents_doc),
        ("extractions.json", extractions_doc),
    ):
        if doc and doc.get("synthetic") is not True:
            fail(f"{name}: must set \"synthetic\": true")

    # ---------------- study / eCRF ----------------
    study_obj = study.get("study", {})
    study_id = study_obj.get("id")
    if not study_id:
        fail("study.json: missing study.id")

    sites = study.get("sites", [])
    if len(sites) != 3:
        fail(f"study.json: expected 3 sites, found {len(sites)}")
    site_ids = {s.get("id") for s in sites}
    if len(site_ids) != len(sites):
        fail("study.json: duplicate site ids")

    schedule = study.get("visitSchedule", [])
    if not schedule:
        fail("study.json: missing visitSchedule")
    visit_ids = {v.get("visitId") for v in schedule}

    ecrf = study.get("ecrf", {})
    fields = ecrf.get("fields", [])
    if not 10 <= len(fields) <= 15:
        fail(f"study.json: expected 10-15 eCRF fields, found {len(fields)}")
    field_by_id = {}
    section_ids = {s.get("id") for s in ecrf.get("sections", [])}
    for f in fields:
        fid = f.get("id")
        if not fid:
            fail("study.json: eCRF field without id")
            continue
        if fid in field_by_id:
            fail(f"study.json: duplicate field id {fid}")
        field_by_id[fid] = f
        if f.get("section") not in section_ids:
            fail(f"study.json: field {fid} has unknown section {f.get('section')}")
        term = f.get("terminology")
        if term is not None and not isinstance(term.get("codeVerified"), bool):
            fail(f"study.json: field {fid} terminology needs boolean codeVerified")
        if term and term.get("codeVerified") is False and not term.get("display"):
            fail(f"study.json: unverified code on {fid} needs a display string")

    # ---------------- documents ----------------
    doc_entries = documents_doc.get("documents", [])
    if not doc_entries:
        fail("documents.json: no documents")
    doc_by_id: dict[str, dict] = {}
    doc_text: dict[str, str] = {}
    for entry in doc_entries:
        did = entry.get("id")
        if not did:
            fail("documents.json: entry without id")
            continue
        if did in doc_by_id:
            fail(f"documents.json: duplicate document id {did}")
        doc_by_id[did] = entry
        asset_path = entry.get("assetPath", "")
        if not asset_path:
            fail(f"documents.json: {did} has no assetPath")
            continue
        path = APP / asset_path
        if not path.exists():
            fail(f"documents.json: {did} file not found: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        doc_text[did] = text
        encoded = text.encode("utf-8")
        if entry.get("charLength") != len(text):
            fail(f"{did}: charLength {entry.get('charLength')} != {len(text)}")
        digest = hashlib.sha256(encoded).hexdigest()
        if entry.get("sha256") != digest:
            fail(f"{did}: sha256 mismatch (file changed without regenerating?)")
        check_banner(did, text)
        if any(ord(ch) > 0xFFFF for ch in text):
            fail(f"{did}: non-BMP character found; spans must stay UTF-16 safe")

    # ---------------- participants ----------------
    parts = participants_doc.get("participants", [])
    if not 6 <= len(parts) <= 10:
        fail(f"participants.json: expected 6-10 participants, found {len(parts)}")
    part_by_id: dict[str, dict] = {}
    for p in parts:
        pid = p.get("id")
        if not pid:
            fail("participants.json: participant without id")
            continue
        if pid in part_by_id:
            fail(f"participants.json: duplicate participant id {pid}")
        part_by_id[pid] = p
        if p.get("studyId") != study_id:
            fail(f"{pid}: studyId {p.get('studyId')} != {study_id}")
        if p.get("siteId") not in site_ids:
            fail(f"{pid}: unknown siteId {p.get('siteId')}")
        if p.get("status") not in PARTICIPANT_STATUSES:
            fail(f"{pid}: invalid status {p.get('status')}")
        if not isinstance(p.get("age"), int):
            fail(f"{pid}: age must be an integer")
        if p.get("sex") not in {"F", "M"}:
            fail(f"{pid}: sex must be F or M")
        for v in p.get("visits", []):
            if v.get("status") not in VISIT_STATUSES:
                fail(f"{pid}: invalid visit status {v.get('status')}")
            if not v.get("date"):
                fail(f"{pid}: visit {v.get('name')} has no date")
        for e in p.get("ecrfs", []):
            if e.get("status") not in ECRF_STATUSES:
                fail(f"{pid}: invalid eCRF status {e.get('status')}")
            pct = e.get("completePct")
            if not isinstance(pct, int) or not 0 <= pct <= 100:
                fail(f"{pid}: completePct must be 0..100, got {pct}")
        for issue in p.get("issues", []):
            if issue.get("field") and issue["field"] not in field_by_id:
                fail(f"{pid}: issue references unknown field {issue['field']}")
        for did in p.get("documentIds", []):
            if did not in doc_by_id:
                fail(f"{pid}: references unknown document {did}")

    if not 2 <= len({d.get("participantId") for d in doc_entries}) <= 3:
        fail("documents.json: documents must cover 2-3 key participants")
    docs_per_participant: dict[str, int] = {}
    for entry in doc_entries:
        docs_per_participant[entry.get("participantId")] = (
            docs_per_participant.get(entry.get("participantId"), 0) + 1
        )
    for pid, count in docs_per_participant.items():
        if not 3 <= count <= 5:
            fail(f"{pid}: expected 3-5 documents, found {count}")
        if pid not in part_by_id:
            fail(f"documents.json: unknown participant {pid}")
        elif sorted(part_by_id[pid].get("documentIds", [])) != sorted(
            e["id"] for e in doc_entries if e.get("participantId") == pid
        ):
            fail(f"{pid}: participant.documentIds does not match documents.json")

    # ---------------- extractions ----------------
    rows = extractions_doc.get("extractions", [])
    if not rows:
        fail("extractions.json: no extractions")
    seen_ids = set()
    kind_count = {"low_confidence": 0, "wrong_value": 0, "abstention": 0}

    for row in rows:
        eid = row.get("id")
        if not eid:
            fail("extractions.json: extraction without id")
            continue
        if eid in seen_ids:
            fail(f"extractions.json: duplicate extraction id {eid}")
        seen_ids.add(eid)

        did = row.get("documentId")
        if did not in doc_by_id:
            fail(f"{eid}: unknown documentId {did}")
            continue
        if row.get("participantId") != doc_by_id[did].get("participantId"):
            fail(f"{eid}: participantId does not match document owner")

        fid = row.get("field")
        if fid not in field_by_id:
            fail(f"{eid}: unknown eCRF field {fid}")
            continue
        if row.get("fieldLabel") != field_by_id[fid].get("label"):
            fail(f"{eid}: fieldLabel does not match study.json")

        status = row.get("status")
        if status not in EXTRACTION_STATUSES:
            fail(f"{eid}: invalid status {status}")
        conf = row.get("confidence")
        if not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
            fail(f"{eid}: confidence must be 0..1, got {conf}")

        if not isinstance(row.get("value"), str) or not row["value"].strip():
            fail(f"{eid}: value must be a non-empty display string")

        expected_model = extractions_doc.get("generator", {}).get("modelId")
        if expected_model and row.get("model") != expected_model:
            fail(f"{eid}: model id drift")
        if not row.get("promptVersion"):
            fail(f"{eid}: missing promptVersion")

        text = doc_text.get(did)
        if text is None:
            continue
        if row.get("sourceText") != text:
            fail(f"{eid}: embedded sourceText differs from {did}.txt")

        evidence = row.get("evidence") or []
        if status == "abstained":
            if not row.get("abstentionReason"):
                fail(f"{eid}: abstention needs abstentionReason")
            if row.get("proposedCode") is not None:
                fail(f"{eid}: abstention must not carry a proposedCode")
            if conf != 0:
                fail(f"{eid}: abstention confidence must be 0")
        else:
            if row.get("abstentionReason") is not None:
                fail(f"{eid}: proposed value must not have abstentionReason")
            if not evidence:
                fail(f"{eid}: proposed value needs at least one evidence span")
            term = field_by_id[fid].get("terminology")
            if term and row.get("proposedCode") is None:
                fail(f"{eid}: field {fid} has target terminology but no proposedCode")

        if row.get("spanStart") != (evidence[0]["start"] if evidence else 0) or \
                row.get("spanEnd") != (evidence[0]["end"] if evidence else 0):
            fail(f"{eid}: primary spanStart/spanEnd differs from evidence[0]")

        for idx, ev in enumerate(evidence):
            start, end = ev.get("start"), ev.get("end")
            label = f"{eid} evidence[{idx}]"
            if not isinstance(start, int) or not isinstance(end, int):
                fail(f"{label}: start/end must be integers")
                continue
            if not 0 <= start < end <= len(text):
                fail(f"{label}: span {start}..{end} outside 0..{len(text)}")
                continue
            actual = text[start:end]
            if ev.get("text") != actual:
                fail(f"{label}: text mismatch; expected {actual!r}, got {ev.get('text')!r}")
            if not actual.strip():
                fail(f"{label}: whitespace-only span")

        code = row.get("proposedCode")
        if code is not None:
            if not code.get("system") or not code.get("display"):
                fail(f"{eid}: proposedCode needs system and display")
            if not isinstance(code.get("codeVerified"), bool):
                fail(f"{eid}: proposedCode needs boolean codeVerified")

        seeded = row.get("seededIssue")
        if seeded:
            kind = seeded.get("kind")
            if kind not in kind_count:
                fail(f"{eid}: unknown seededIssue.kind {kind}")
            else:
                kind_count[kind] += 1

    # ---------------- seeded demo cases ----------------
    cases = extractions_doc.get("seededDemoCases", {})
    row_by_id = {r.get("id"): r for r in rows}

    low = cases.get("lowConfidence", {})
    low_row = row_by_id.get(low.get("extractionId"))
    if not low_row:
        fail("seededDemoCases.lowConfidence does not resolve")
    elif not low_row["confidence"] < 0.5:
        fail("seededDemoCases.lowConfidence is not below 0.5")
    elif not any(r["confidence"] < 0.5 for r in rows):
        fail("no low-confidence extraction found")

    wrong = cases.get("wrongValue", {})
    wrong_row = row_by_id.get(wrong.get("extractionId"))
    if not wrong_row:
        fail("seededDemoCases.wrongValue does not resolve")
    else:
        if wrong_row.get("normalizedValue") == wrong.get("expectedCorrectValue"):
            fail("wrongValue proposal already equals the expected correct value")
        expected = wrong.get("expectedCorrectValue")
        if expected and expected.lower() not in wrong_row.get("sourceText", "").lower():
            fail("wrongValue: correct value does not appear in the source text")

    abst = cases.get("abstention", {})
    abst_row = row_by_id.get(abst.get("extractionId"))
    if not abst_row:
        fail("seededDemoCases.abstention does not resolve")
    elif abst_row.get("status") != "abstained":
        fail("seededDemoCases.abstention is not an abstained extraction")

    for kind, count in kind_count.items():
        if count < 1:
            fail(f"no extraction marked as seeded {kind}")

    # ---------------- dashboard ----------------
    if dashboard:
        dash_study_ids = {s.get("id") for s in dashboard.get("studies", [])}
        if study_id not in dash_study_ids:
            fail("dashboard.json: study id does not match study.json")
        for site in dashboard.get("sites", []):
            if site.get("id") not in site_ids:
                fail(f"dashboard.json: unknown site {site.get('id')}")
        for task in dashboard.get("tasks", []):
            pid = task.get("participantId")
            if pid and pid not in part_by_id:
                fail(f"dashboard.json: task references unknown participant {pid}")

    # ---------------- report ----------------
    span_total = sum(len(r.get("evidence") or []) for r in rows)
    if errors:
        print(f"FAIL: {len(errors)} validation error(s)")
        for msg in errors:
            print(f"  - {msg}")
        return 1
    print("PASS")
    print(f"  study: 1 | sites: {len(sites)} | eCRF fields: {len(fields)} "
          f"| visit rows: {len(schedule)}")
    print(f"  participants: {len(parts)} | documents: {len(doc_entries)} "
          f"| extractions: {len(rows)} | evidence spans checked: {span_total}")
    print("  seeded cases: low_confidence="
          f"{kind_count['low_confidence']}, wrong_value={kind_count['wrong_value']}, "
          f"abstention={kind_count['abstention']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
