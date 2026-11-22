"""Screening evaluation harness against the seeded truth.

Evaluates the AI screening checker (`rules` and `ollama`) across the seeded
Hospital-2 cohort (5 baseline + 2 arrivals) and Hospital-1 screening patients,
checking per-criterion verdicts (`met | not_met | unknown`), overall eligibility
(`eligible | screen_fail | unknown`), and exact evidence span integrity.
"""
from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.ai import screening
from app.ai.span import span_matches

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
SEED_SOURCE = ROOT / "fhir-seed" / "source"
APP_DATA = ROOT / "app" / "assets" / "data"
RESULTS = Path(__file__).resolve().parent / "results"

# Seeded ground truth for the 7 Hospital-2 patients + 4 Hospital-1 patients with documents
SCREENING_TRUTH: dict[str, dict[str, Any]] = {
    "GBM-NL-201": {
        "overall": "eligible",
        "criteria": {
            "INC-01": "met",
            "INC-02": "met",
            "INC-03": "met",
            "INC-04": "met",
            "INC-05": "met",
            "INC-06": "met",
            "INC-07": "met",
            "INC-08": "met",
            "INC-09": "met",
            "EXC-01": "met",
            "EXC-02": "met",
            "EXC-03": "met",
            "EXC-04": "met",
        },
    },
    "GBM-NL-202": {
        "overall": "eligible",
        "criteria": {
            "INC-01": "met",
            "INC-02": "met",
            "INC-03": "met",
            "INC-04": "met",
            "INC-05": "met",
            "INC-06": "met",
            "INC-07": "met",
            "INC-08": "met",
            "INC-09": "met",
            "EXC-01": "met",
            "EXC-02": "met",
            "EXC-03": "met",
            "EXC-04": "met",
        },
    },
    "GBM-NL-203": {
        "overall": "screen_fail",
        "criteria": {
            "INC-01": "met",
            "INC-02": "met",
            "INC-03": "met",
            "INC-04": "not_met",  # KPS 50% < 60%
            "INC-05": "met",
            "INC-06": "met",
            "INC-07": "met",
            "INC-08": "met",
            "INC-09": "met",
            "EXC-01": "met",
            "EXC-02": "met",
            "EXC-03": "met",
            "EXC-04": "met",
        },
    },
    "GBM-NL-204": {
        "overall": "unknown",
        "criteria": {
            "INC-01": "met",
            "INC-02": "met",
            "INC-03": "unknown",  # MGMT assay pending
            "INC-04": "met",
            "INC-05": "met",
            "INC-06": "met",
            "INC-07": "met",
            "INC-08": "met",
            "INC-09": "met",
            "EXC-01": "met",
            "EXC-02": "met",
            "EXC-03": "met",
            "EXC-04": "met",
        },
    },
    "GBM-NL-205": {
        "overall": "screen_fail",
        "criteria": {
            "INC-01": "met",
            "INC-02": "not_met",  # IDH-mutant
            "INC-03": "met",
            "INC-04": "met",
            "INC-05": "met",
            "INC-06": "met",
            "INC-07": "met",
            "INC-08": "met",
            "INC-09": "met",
            "EXC-01": "met",
            "EXC-02": "met",
            "EXC-03": "not_met",  # IDH-mutant triggers EXC-03
            "EXC-04": "met",
        },
    },
    "GBM-NL-206": {
        "overall": "eligible",
        "criteria": {
            "INC-01": "met",
            "INC-02": "met",
            "INC-03": "met",
            "INC-04": "met",
            "INC-05": "met",
            "INC-06": "met",
            "INC-07": "met",
            "INC-08": "met",
            "INC-09": "met",
            "EXC-01": "met",
            "EXC-02": "met",
            "EXC-03": "met",
            "EXC-04": "met",
        },
    },
    "GBM-NL-207": {
        "overall": "unknown",
        "criteria": {
            "INC-01": "met",
            "INC-02": "unknown",
            "INC-03": "unknown",
            "INC-04": "met",
            "INC-05": "unknown",
            "INC-06": "unknown",
            "INC-07": "unknown",
            "INC-08": "unknown",
            "INC-09": "unknown",
            "EXC-01": "met",
            "EXC-02": "met",
            "EXC-03": "unknown",
            "EXC-04": "met",
        },
    },
    "GBM-NL-011": {
        "overall": "unknown",
        "criteria": {
            "INC-01": "met",
            "INC-02": "unknown",
            "INC-03": "unknown",
            "INC-04": "met",
            "INC-05": "unknown",
            "INC-06": "unknown",
            "INC-07": "unknown",
            "INC-08": "unknown",
            "INC-09": "unknown",
            "EXC-01": "unknown",
            "EXC-02": "met",
            "EXC-03": "unknown",
            "EXC-04": "unknown",
        },
    },
}


def load_patient_documents() -> dict[str, list[dict[str, Any]]]:
    """Load source documents per participant from hospital 2, hospital 1 arrivals, and baseline."""
    by_patient: dict[str, list[dict[str, Any]]] = {}

    # Hospital 2 baseline + arrivals
    h2_path = SEED_SOURCE / "hospital2.json"
    if h2_path.exists():
        h2 = json.loads(h2_path.read_text(encoding="utf-8"))
        for group in ("baseline", "arrivals"):
            for p in h2.get(group, []):
                docs = []
                for d in p.get("documents", []):
                    text = (SEED_SOURCE / "documents" / d["file"]).read_text(encoding="utf-8")
                    docs.append({
                        "id": d["id"],
                        "participantId": p["id"],
                        "type": d["type"],
                        "title": d["title"],
                        "language": d.get("language"),
                        "documentDate": d.get("documentDate"),
                        "text": text,
                    })
                by_patient[p["id"]] = docs

    # Hospital 1 arrivals
    arr_path = SEED_SOURCE / "arrivals.json"
    if arr_path.exists():
        arr = json.loads(arr_path.read_text(encoding="utf-8"))
        for p in arr.get("participants", []):
            docs = []
            for d in p.get("documents", []):
                text = (SEED_SOURCE / "documents" / d["file"]).read_text(encoding="utf-8")
                docs.append({
                    "id": d["id"],
                    "participantId": p["id"],
                    "type": d["type"],
                    "title": d["title"],
                    "language": d.get("language"),
                    "documentDate": d.get("documentDate"),
                    "text": text,
                })
            by_patient[p["id"]] = docs

    return by_patient


def evaluate_screening(provider_name: str = "rules") -> dict[str, Any]:
    t0 = time.perf_counter()
    criteria = screening.load_criteria()
    docs_by_patient = load_patient_documents()

    total_checks = 0
    correct_checks = 0
    span_errors = 0
    overall_correct = 0
    patient_rows: list[dict[str, Any]] = []
    per_criterion: dict[str, dict[str, Any]] = {
        c.id: {"id": c.id, "type": c.type, "support": 0, "correct": 0, "spanErrors": 0}
        for c in criteria
    }
    mismatches: list[dict[str, Any]] = []

    for pid, expected in SCREENING_TRUTH.items():
        docs = docs_by_patient.get(pid, [])
        docs_map = {d["id"]: d["text"] for d in docs}
        res = screening.check_participant(
            pid, docs, criteria=criteria, provider=provider_name, allow_fallback=False
        )
        if res.overall == expected["overall"]:
            overall_correct += 1
        by_cid = res.by_criterion()
        p_correct = 0
        p_span_errors = 0
        for cid, exp_verdict in expected["criteria"].items():
            total_checks += 1
            per_criterion[cid]["support"] += 1
            chk = by_cid.get(cid)
            pred_verdict = chk.verdict if chk else "unknown"
            if pred_verdict == exp_verdict:
                correct_checks += 1
                p_correct += 1
                per_criterion[cid]["correct"] += 1
            else:
                mismatches.append({
                    "participantId": pid,
                    "criterionId": cid,
                    "expected": exp_verdict,
                    "predicted": pred_verdict,
                    "rationale": chk.rationale if chk else None,
                })
            if chk and chk.verdict in ("met", "not_met"):
                doc_text = docs_map.get(chk.document_id or "")
                if not doc_text or not chk.evidence or not all(span_matches(doc_text, e) for e in chk.evidence):
                    span_errors += 1
                    p_span_errors += 1
                    per_criterion[cid]["spanErrors"] += 1

        patient_rows.append({
            "participantId": pid,
            "expectedOverall": expected["overall"],
            "predictedOverall": res.overall,
            "overallMatch": res.overall == expected["overall"],
            "criteriaCorrect": p_correct,
            "criteriaTotal": len(expected["criteria"]),
            "spanErrors": p_span_errors,
        })

    for slot in per_criterion.values():
        slot["accuracy"] = round(slot["correct"] / slot["support"], 4) if slot["support"] else None

    accuracy = round(correct_checks / total_checks, 4) if total_checks else None
    overall_accuracy = round(overall_correct / len(SCREENING_TRUTH), 4) if SCREENING_TRUTH else None
    duration_ms = int((time.perf_counter() - t0) * 1000)

    return {
        "schemaVersion": 1,
        "generatedAt": datetime.now(UTC).isoformat(),
        "provider": provider_name,
        "summary": {
            "patients": len(SCREENING_TRUTH),
            "criteriaPerPatient": len(criteria),
            "totalChecks": total_checks,
            "correctChecks": correct_checks,
            "criterionAccuracy": accuracy,
            "overallAccuracy": overall_accuracy,
            "spanErrors": span_errors,
            "durationMs": duration_ms,
        },
        "patients": patient_rows,
        "criteria": list(per_criterion.values()),
        "mismatches": mismatches,
    }


def save_screening_eval(result: dict[str, Any], out_dir: Path | None = None) -> Path:
    out_dir = out_dir or RESULTS
    out_dir.mkdir(parents=True, exist_ok=True)
    provider = result["provider"]
    path = out_dir / f"latest-screening-{provider}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "latest-screening.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return path
