"""Precision / recall / F1 / abstention eval harness.

Runs a provider over gold-labelled documents and scores each (document, field)
label. Proposal scoring:

* gold proposed + predicted proposed with the same normalised value -> TP
* gold proposed + predicted proposed with another value        -> FP and FN
* gold proposed + predicted abstained                          -> FN
* gold abstained + predicted proposed                          -> FP
* gold abstained + predicted abstained                         -> correct abstention

Span integrity is checked on every proposal before it counts.
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.ai import providers
from app.ai.providers import rules as rules_mod
from app.ai.span import span_matches
from app.ai.types import ExtractionResult, FieldDef

from . import gold as gold_mod

RESULTS = Path(__file__).resolve().parent / "results"


def _eq(field: str, a: Any, b: Any) -> bool:
    if a is None or b is None:
        return False
    if field in ("AGE", "KPS", "RTFRAC", "TMZPLNC", "AEGRADE", "RTDOSE"):
        try:
            return abs(float(a) - float(b)) < 1e-6
        except (TypeError, ValueError):
            return False
    return str(a).strip().casefold() == str(b).strip().casefold()


def _rate(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def _f1(p: float | None, r: float | None) -> float | None:
    if p is None or r is None or (p + r) == 0:
        return None
    return round(2 * p * r / (p + r), 4)


def evaluate(provider_name: str, *, dataset: str = "all", prompt_version: str | None = None,
             docs_subset: list[str] | None = None) -> dict[str, Any]:
    provider = providers.get_provider(provider_name)
    ok, reason = provider.available()
    if not ok:
        raise RuntimeError(f"provider {provider_name} unavailable: {reason}")

    docs, gold, dataset_meta = gold_mod.load_set(dataset)
    if docs_subset:
        docs = [d for d in docs if d["id"] in docs_subset]
    fields = {f["id"]: f for f in gold_mod.load_fields()}
    field_defs = [FieldDef.from_api(f) for f in fields.values()]

    per_field: dict[str, dict[str, Any]] = {
        fid: {"field": fid, "label": f.get("label", fid), "support": 0, "goldAbstentions": 0,
              "abstentions": 0, "abstentionsCorrect": 0, "tp": 0, "fp": 0, "fn": 0,
              "proposed": 0, "confidenceSum": 0.0, "spanErrors": 0}
        for fid, f in fields.items()
    }
    doc_rows: list[dict[str, Any]] = []
    pred_cache: dict[str, dict] = {}
    value_errors: list[dict[str, Any]] = []
    span_errors_total = 0
    total_tp = total_fp = total_fn = total_gold_abstain = total_abstain = total_abstain_correct = 0
    total_gold_proposals = 0
    wall0 = time.perf_counter()
    prompt_tag = prompt_hash = None
    warnings: list[str] = []

    for d in docs:
        t0 = time.perf_counter()
        result: ExtractionResult = provider.extract(d["text"], d["type"], field_defs,
                                                    prompt_version=prompt_version)
        prompt_tag = result.metadata.prompt_version
        prompt_hash = result.metadata.prompt_hash
        warnings.extend(result.metadata.warnings)
        pred = result.by_field()
        pred_cache[d["id"]] = pred
        g = gold.get(d["id"], {})
        matched = mismatched = missing = unexpected = abstained = low = 0
        invalid_spans = 0
        for p in result.proposals:
            if p.status == "proposed":
                if not p.evidence or not all(span_matches(d["text"], e) for e in p.evidence):
                    invalid_spans += 1
                if p.confidence < 0.6:
                    low += 1
            else:
                abstained += 1
        span_errors_total += invalid_spans
        for fid, expected in g.items():
            slot = per_field[fid]
            p = pred.get(fid)
            if expected["status"] == "abstained":
                total_gold_abstain += 1
                slot["goldAbstentions"] += 1
                if p is None or p.status == "abstained":
                    slot["abstentionsCorrect"] += 1
                    slot["abstentions"] += 1
                    total_abstain_correct += 1
                    total_abstain += 1
                else:
                    slot["abstentions"] += 1
                    slot["fp"] += 1
                    total_abstain += 1
                    total_fp += 1
                    mismatched += 1
                    value_errors.append({"documentId": d["id"], "field": fid, "gold": "abstained",
                                         "predicted": p.value, "kind": "proposed_when_abstain"})
                slot["support"] += 1
                continue
            total_gold_proposals += 1
            slot["support"] += 1
            if p is None or p.status == "abstained":
                slot["fn"] += 1
                slot["abstentions"] += 1
                total_fn += 1
                total_abstain += 1
                missing += 1
                value_errors.append({"documentId": d["id"], "field": fid, "gold": expected["value"],
                                     "predicted": "abstained", "kind": "missed"})
                continue
            slot["proposed"] += 1
            slot["confidenceSum"] += p.confidence
            if _eq(fid, expected["normalizedValue"], p.normalized_value):
                slot["tp"] += 1
                total_tp += 1
                matched += 1
            else:
                slot["fp"] += 1
                slot["fn"] += 1
                total_fp += 1
                total_fn += 1
                mismatched += 1
                value_errors.append({"documentId": d["id"], "field": fid, "gold": expected["value"],
                                     "predicted": p.value, "kind": "wrong_value"})
        # proposals for fields the gold set does not label for this document are not scored
        unexpected = sum(1 for p in result.proposals if p.field not in g)
        doc_rows.append({
            "documentId": d["id"], "participantId": d.get("participantId"), "type": d["type"],
            "durationMs": int((time.perf_counter() - t0) * 1000),
            "proposals": sum(1 for p in result.proposals if p.status == "proposed"),
            "abstained": abstained, "lowConfidence": low,
            "matched": matched, "mismatched": mismatched, "missing": missing,
            "unlabelledProposals": unexpected, "spanErrors": invalid_spans,
            "warnings": result.metadata.warnings,
        })

    for slot in per_field.values():
        slot["precision"] = _rate(slot["tp"], slot["tp"] + slot["fp"])
        slot["recall"] = _rate(slot["tp"], slot["tp"] + slot["fn"])
        slot["f1"] = _f1(slot["precision"], slot["recall"])
        slot["abstentionRate"] = _rate(slot["abstentions"], slot["support"])
        slot["abstentionRecall"] = _rate(slot["abstentionsCorrect"], slot["goldAbstentions"])
        slot["meanConfidence"] = round(slot["confidenceSum"] / slot["proposed"], 4) if slot["proposed"] else None
        del slot["confidenceSum"]

    f1s = [x["f1"] for x in per_field.values() if x["support"] and x["f1"] is not None]
    precision = _rate(total_tp, total_tp + total_fp)
    recall = _rate(total_tp, total_tp + total_fn)

    result = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(UTC).isoformat(),
        "provider": {"name": provider.name, "model": provider.model, "paid": provider.paid},
        "prompt": {"version": prompt_tag, "sha256": prompt_hash},
        "dataset": dataset_meta,
        "summary": {
            "documents": len(docs),
            "durationMs": int((time.perf_counter() - wall0) * 1000),
            "goldProposals": total_gold_proposals,
            "goldAbstentions": total_gold_abstain,
            "truePositives": total_tp,
            "falsePositives": total_fp,
            "falseNegatives": total_fn,
            "precision": precision,
            "recall": recall,
            "f1": _f1(precision, recall),
            "macroF1": round(sum(f1s) / len(f1s), 4) if f1s else None,
            "abstentionRate": _rate(total_abstain, total_gold_proposals + total_gold_abstain),
            "abstentionRecall": _rate(total_abstain_correct, total_gold_abstain),
            "spanErrors": span_errors_total,
            "warnings": len(warnings),
        },
        "fields": list(per_field.values()),
        "documents": doc_rows,
        "hardCases": _hard_cases(provider.name, pred_cache=pred_cache),
        "valueErrors": value_errors[:50],
        "warnings": warnings[:50],
    }
    return result


def _hard_cases(provider_name: str, *, pred_cache: dict[str, dict]) -> dict[str, Any]:
    cases: dict[str, Any] = {}

    def pred(doc: str, field: str):
        bucket = pred_cache.get(doc) or {}
        p = bucket.get(field)
        if p is None:
            return {"status": "missing"}
        return {"status": p.status, "value": p.value, "normalizedValue": p.normalized_value,
                "confidence": p.confidence, "evidence": [e.text for e in p.evidence]}

    if "DOC-002-PATH" in pred_cache:
        wrong = pred("DOC-002-PATH", "MGMTPROM")
        cases["wrongValue"] = {
        "documentId": "DOC-002-PATH", "field": "MGMTPROM", "expected": "unmethylated",
        "prediction": wrong,
            "pass": wrong.get("status") == "proposed" and _eq("MGMTPROM", "unmethylated",
                                                              wrong.get("normalizedValue")),
        }
    if "DOC-002-MRI" in pred_cache:
        low = pred("DOC-002-MRI", "EXTRES")
        cases["lowConfidence"] = {
            "documentId": "DOC-002-MRI", "field": "EXTRES", "expected": "confidence < 0.6",
            "prediction": low,
            "pass": low.get("status") == "proposed" and (low.get("confidence") or 0) < 0.6,
        }
    if "DOC-003-MRI" in pred_cache:
        abst = pred("DOC-003-MRI", "PROGDAT")
        cases["abstention"] = {
            "documentId": "DOC-003-MRI", "field": "PROGDAT", "expected": "abstained",
            "prediction": abst, "pass": abst.get("status") == "abstained",
        }
    if "DOC-005-MRI" in pred_cache:
        held = pred("DOC-005-MRI", "PROGDAT")
        cases["arrivalsAbstention"] = {
            "documentId": "DOC-005-MRI", "field": "PROGDAT", "expected": "abstained",
            "prediction": held, "pass": held.get("status") == "abstained",
        }
    cases["allPass"] = all(v["pass"] for v in cases.values())
    return cases


def save(result: dict[str, Any], out_dir: Path | None = None, *,
         update_latest: bool = True) -> tuple[Path, Path]:
    out_dir = out_dir or RESULTS
    out_dir.mkdir(parents=True, exist_ok=True)
    provider = result["provider"]["name"]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_path = out_dir / f"{provider}-{stamp}.json"
    run_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    (out_dir / f"latest-{provider}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    md = to_markdown(result)
    (out_dir / f"latest-{provider}.md").write_text(md + "\n")
    if update_latest:
        (out_dir / "latest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        (out_dir / "latest.md").write_text(md + "\n")
    return run_path, out_dir / f"latest-{provider}.md"


def _fmt(x: float | None) -> str:
    return "—" if x is None else f"{x:.3f}"


def to_markdown(result: dict[str, Any]) -> str:
    s = result["summary"]
    p = result["provider"]
    lines = [
        f"# AI extraction eval — {p['name']} ({p['model']})",
        "",
        f"Dataset: **{result['dataset']['name']}** · {s['documents']} documents · "
        f"prompt `{result['prompt']['version']}` · {s['durationMs']} ms",
        "",
        f"**Precision {_fmt(s['precision'])} · Recall {_fmt(s['recall'])} · F1 {_fmt(s['f1'])} · "
        f"macro-F1 {_fmt(s['macroF1'])} · abstention rate {_fmt(s['abstentionRate'])} · "
        f"span errors {s['spanErrors']}**",
        "",
        "| Field | Support | Precision | Recall | F1 | Abstention rate | Mean confidence |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for f in result["fields"]:
        if not f["support"]:
            continue
        lines.append(f"| {f['field']} ({f['label']}) | {f['support']} | {_fmt(f['precision'])} | "
                     f"{_fmt(f['recall'])} | {_fmt(f['f1'])} | {_fmt(f['abstentionRate'])} | "
                     f"{_fmt(f['meanConfidence'])} |")
    lines += ["", "## Seeded hard cases", ""]
    for name, case in result["hardCases"].items():
        if name == "allPass":
            continue
        pred = case["prediction"]
        lines.append(f"- **{name}** ({case['documentId']} / {case['field']}): "
                     f"{'PASS' if case['pass'] else 'FAIL'} — expected {case['expected']}, "
                     f"got {pred.get('status')} {pred.get('value') or pred.get('normalizedValue') or ''}"
                     f" (confidence {pred.get('confidence')})")
    lines += ["", f"Hard cases all pass: **{'yes' if result['hardCases'].get('allPass') else 'no'}**", ""]
    return "\n".join(lines)
