"""Run the independently labelled Dutch challenge set against a local provider.

Gold labels are opened by the scorer only, after each provider call. They are
never included in extraction input or prompts.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from app.ai import providers
from app.ai.types import FieldDef

HERE = Path(__file__).resolve().parent


def eq(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    return str(a).strip().casefold() == str(b).strip().casefold()


def evaluate(provider_name="rules"):
    # Load only passages before running provider; labels are loaded below, by scorer.
    source = json.loads((HERE / "documents.json").read_text())
    documents = source["documents"]
    study = json.loads((BACKEND.parent / "app/assets/data/study.json").read_text())
    fields = [FieldDef.from_api(f) for f in study["ecrf"]["fields"]]
    provider = providers.get_provider(provider_name)
    available, reason = provider.available()
    if not available:
        raise RuntimeError(reason)

    predictions = {}
    for doc in documents:
        result = provider.extract(doc["text"], doc["type"], fields)
        predictions[doc["id"]] = result

    gold_data = json.loads((HERE / "gold.json").read_text())["documents"]
    slots = defaultdict(lambda: {"support": 0, "correct": 0, "tp": 0, "fp": 0, "fn": 0,
                                 "goldAbstentions": 0, "correctAbstentions": 0,
                                 "spanSupport": 0, "exactSpan": 0, "spanErrors": 0})
    rows = []
    total_span_proposals = exact_span_proposals = gold_span_count = total_abstain = gold_abstain = correct_abstain = 0
    for doc in documents:
        pred_by_field = predictions[doc["id"]].by_field()
        for field, expected in gold_data[doc["id"]].items():
            s = slots[field]
            s["support"] += 1
            pred = pred_by_field.get(field)
            proposed = pred is not None and pred.status == "proposed"
            expected_proposed = expected["status"] == "proposed"
            if expected_proposed:
                gold_span_count += 1
            value_correct = ((proposed and expected_proposed and eq(expected["value"], pred.normalized_value))
                             or (not proposed and not expected_proposed))
            if value_correct:
                s["correct"] += 1
                if expected_proposed:
                    s["tp"] += 1
            elif proposed and expected_proposed:
                s["fp"] += 1
                s["fn"] += 1
            elif proposed and not expected_proposed:
                s["fp"] += 1
            elif expected_proposed:
                s["fn"] += 1
            abstained = not proposed
            if abstained:
                total_abstain += 1
            if not expected_proposed:
                gold_abstain += 1
                s["goldAbstentions"] += 1
                if abstained:
                    correct_abstain += 1
                    s["correctAbstentions"] += 1
            if proposed:
                total_span_proposals += 1
                s["spanSupport"] += 1
                evidence = [e.text for e in pred.evidence]
                valid = bool(evidence) and all(e in doc["text"] for e in evidence)
                if not valid:
                    s["spanErrors"] += 1
                if expected_proposed and expected["evidenceSpan"] in evidence:
                    exact_span_proposals += 1
                    s["exactSpan"] += 1
            rows.append({"documentId": doc["id"], "field": field,
                         "goldStatus": expected["status"],
                         "predictedStatus": pred.status if pred else "missing",
                         "goldValue": expected["value"],
                         "predictedValue": pred.normalized_value if proposed else None,
                         "valueCorrect": bool(value_correct),
                         "goldSpan": expected["evidenceSpan"],
                         "predictedSpans": [e.text for e in pred.evidence] if proposed else [],
                         "exactSpan": bool(proposed and expected_proposed and expected["evidenceSpan"] in [e.text for e in pred.evidence])})
    per_field = {}
    for field, s in sorted(slots.items()):
        den_p = s["tp"] + s["fp"]
        den_r = s["tp"] + s["fn"]
        precision = s["tp"] / den_p if den_p else 0.0
        recall = s["tp"] / den_r if den_r else 0.0
        per_field[field] = {**s, "accuracy": round(s["correct"] / s["support"], 4),
                            "precision": round(precision, 4), "recall": round(recall, 4),
                            "f1": round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0,
                            "abstentionRecall": round(s["correctAbstentions"] / s["goldAbstentions"], 4) if s["goldAbstentions"] else None,
                            "exactSpanRate": round(s["exactSpan"] / s["spanSupport"], 4) if s["spanSupport"] else None}
    tp = sum(s["tp"] for s in slots.values())
    fp = sum(s["fp"] for s in slots.values())
    fn = sum(s["fn"] for s in slots.values())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    spans_errors = sum(s["spanErrors"] for s in slots.values())
    prompt_hashes = sorted({p.metadata.prompt_hash for p in predictions.values()})
    prompt_versions = sorted({p.metadata.prompt_version for p in predictions.values()})
    return {
        "schemaVersion": 1, "generatedAt": datetime.now(UTC).isoformat(),
        "dataset": {"name": "independent-dutch-synthetic-challenge", "documents": len(documents),
                    "labelledDocumentFieldPairs": len(rows), "source": "eval/independent_dutch"},
        "provider": {"name": provider.name, "model": provider.model, "paid": provider.paid,
                     "promptVersions": prompt_versions, "promptHashes": prompt_hashes},
        "summary": {"accuracy": round(sum(r["valueCorrect"] for r in rows) / len(rows), 4),
                    "precision": round(precision, 4), "recall": round(recall, 4),
                    "microF1": round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0,
                    "macroF1": round(sum(x["f1"] for x in per_field.values()) / len(per_field), 4),
                    "abstentionRate": round(total_abstain / len(rows), 4),
                    "goldAbstentions": gold_abstain,
                    "correctAbstentions": correct_abstain,
                    "abstentionRecall": round(correct_abstain / gold_abstain, 4) if gold_abstain else None,
                    "exactEvidenceSpanRate": round(exact_span_proposals / total_span_proposals, 4) if total_span_proposals else None,
                    "exactEvidenceSpanRecall": round(exact_span_proposals / gold_span_count, 4) if gold_span_count else None,
                    "spanIntegrityErrors": spans_errors,
                    "spanProposals": total_span_proposals,
                    "exactEvidenceSpans": exact_span_proposals},
        "fields": per_field, "cases": rows,
        "limitations": ["Five fictional documents and 25 labelled document-field pairs; not a clinical estimate.",
                        "Single reference labeler; no inter-rater reliability measurement.",
                        "Small, purposive challenge set with limited vocabulary and report styles."]
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["rules", "ollama"], default="rules")
    ap.add_argument("--out", type=Path, default=HERE.parent / "results/independent_dutch/latest-rules.json")
    args = ap.parse_args()
    result = evaluate(args.provider)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"provider": args.provider, "documents": result["dataset"]["documents"],
                      "labelledPairs": result["dataset"]["labelledDocumentFieldPairs"],
                      "summary": result["summary"], "fields": result["fields"]}, ensure_ascii=False, indent=2))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
