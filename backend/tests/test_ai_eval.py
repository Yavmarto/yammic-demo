"""Eval harness: rules provider must score cleanly and the hard cases must pass."""
from __future__ import annotations

import json

from eval import harness


def test_rules_eval_is_perfect_and_hard_cases_pass(tmp_path):
    result = harness.evaluate("rules", dataset="all")
    s = result["summary"]
    assert s["spanErrors"] == 0
    assert s["precision"] == 1.0
    assert s["recall"] == 1.0
    assert s["f1"] == 1.0
    assert result["hardCases"]["allPass"] is True, result["hardCases"]
    # every field with gold proposals has a defined metric
    fields = {f["field"]: f for f in result["fields"]}
    assert fields["PROGDAT"]["abstentionRate"] == 1.0
    assert fields["EXTRES"]["support"] == 5


def test_eval_result_is_written_and_servable(tmp_path):
    result = harness.evaluate("rules", dataset="arrivals")
    run_path, md_path = harness.save(result, tmp_path)
    assert run_path.exists() and md_path.exists()
    assert (tmp_path / "latest-rules.json").exists()
    assert (tmp_path / "latest.json").exists()
    stored = json.loads((tmp_path / "latest-rules.json").read_text())
    assert stored["provider"]["name"] == "rules"
    assert stored["prompt"]["sha256"]
    assert stored["dataset"]["documents"] == 3
    assert len(stored["fields"]) == 15
