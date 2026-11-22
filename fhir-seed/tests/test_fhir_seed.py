"""Tests for the synthetic FHIR R4 seed bundles.

Run from the repo root:

    python3 -m unittest discover -s fhir-seed/tests -v

These tests are offline: they read the committed bundles and the generator.
The optional integration test runs only when FHIR_INTEGRATION=1 and a local
HAPI server is reachable at FHIR_BASE_URL (default http://127.0.0.1:8090/fhir).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import pathlib
import re
import sys
import unittest

SEED_DIR = pathlib.Path(__file__).resolve().parents[1]
REPO = SEED_DIR.parent
sys.path.insert(0, str(SEED_DIR))

import generate  # noqa: E402

SETS = ("baseline", "arrivals", "hospital2/baseline", "hospital2/arrivals")
ID_PATTERN = re.compile(r"^[A-Za-z0-9\-\.]{1,64}$")


def load_manifest(name: str) -> dict:
    return json.loads((SEED_DIR / name / "manifest.json").read_text(encoding="utf-8"))


def load_bundle(relative: str) -> dict:
    return json.loads((SEED_DIR / relative).read_text(encoding="utf-8"))


def set_resources(name: str) -> dict[tuple[str, str], dict]:
    manifest = load_manifest(name)
    resources: dict[tuple[str, str], dict] = {}
    for relative in manifest["order"]:
        for entry in load_bundle(relative)["entry"]:
            resource = entry["resource"]
            resources[(resource["resourceType"], resource["id"])] = resource
    return resources


def walk_references(node):
    if isinstance(node, dict):
        if set(node.keys()) == {"reference"} or ({"reference"} <= set(node.keys()) and len(node) <= 3):
            yield node["reference"]
        for value in node.values():
            yield from walk_references(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk_references(item)


def walk_resources(name: str):
    manifest = load_manifest(name)
    for relative in manifest["order"]:
        for entry in load_bundle(relative)["entry"]:
            yield relative, entry["resource"]


class ManifestTests(unittest.TestCase):
    def test_manifest_files_exist_in_order(self):
        for name in SETS:
            manifest = load_manifest(name)
            for relative in manifest["order"]:
                self.assertTrue((SEED_DIR / relative).is_file(), relative)

    def test_manifest_counts_match_bundles(self):
        for name in SETS:
            manifest = load_manifest(name)
            counts: dict[str, int] = {}
            for _, resource in walk_resources(name):
                counts[resource["resourceType"]] = counts.get(resource["resourceType"], 0) + 1
            self.assertEqual(dict(sorted(counts.items())), manifest["counts"], name)
            self.assertEqual(sum(counts.values()), manifest["totalResources"], name)
            self.assertEqual(counts.get("DocumentReference", 0), manifest["documentCount"], name)

    def test_patient_counts_and_document_counts(self):
        baseline = load_manifest("baseline")
        arrivals = load_manifest("arrivals")
        h2_baseline = load_manifest("hospital2/baseline")
        h2_arrivals = load_manifest("hospital2/arrivals")
        self.assertEqual(baseline["patientCount"], 8)
        self.assertEqual(baseline["documentCount"], 12)
        self.assertEqual(arrivals["patientCount"], 3)
        self.assertEqual(arrivals["documentCount"], 7)
        self.assertEqual(h2_baseline["patientCount"], 5)
        self.assertEqual(h2_baseline["documentCount"], 13)
        self.assertEqual(h2_arrivals["patientCount"], 2)
        self.assertEqual(h2_arrivals["documentCount"], 5)

    def test_patient_files_match_manifest_hashes(self):
        for name in SETS:
            for patient in load_manifest(name)["patients"]:
                text = (SEED_DIR / patient["file"]).read_text(encoding="utf-8")
                self.assertEqual(hashlib.sha256(text.encode("utf-8")).hexdigest(), patient["sha256"])


class BundleShapeTests(unittest.TestCase):
    def test_bundles_are_transactions_of_puts(self):
        for name in SETS:
            for relative in load_manifest(name)["order"]:
                bundle = load_bundle(relative)
                self.assertEqual(bundle["resourceType"], "Bundle", relative)
                self.assertEqual(bundle["type"], "transaction", relative)
                for entry in bundle["entry"]:
                    resource = entry["resource"]
                    self.assertEqual(entry["request"]["method"], "PUT", relative)
                    expected = f"{resource['resourceType']}/{resource['id']}"
                    self.assertEqual(entry["request"]["url"], expected, relative)
                    self.assertEqual(entry["fullUrl"], f"{generate.SERVER_BASE}/{expected}", relative)

    def test_ids_are_valid_and_unique(self):
        for name in SETS:
            seen: set[tuple[str, str]] = set()
            for _, resource in walk_resources(name):
                key = (resource["resourceType"], resource["id"])
                self.assertRegex(resource["id"], ID_PATTERN, key)
                self.assertNotIn(key, seen, key)
                seen.add(key)

    def test_every_resource_is_marked_synthetic_and_has_narrative(self):
        for name in SETS:
            for relative, resource in walk_resources(name):
                tags = [tag.get("code") for tag in resource.get("meta", {}).get("tag", [])]
                self.assertIn("SYNTHETIC", tags, f"{relative} {resource['resourceType']}/{resource['id']}")
                security = [item.get("code") for item in resource.get("meta", {}).get("security", [])]
                self.assertIn("HTEST", security, f"{relative} {resource['resourceType']}/{resource['id']}")
                text = resource.get("text", {})
                self.assertEqual(text.get("status"), "generated")
                self.assertIn("<div", text.get("div", ""))

    def test_references_resolve_inside_the_set(self):
        for name in SETS:
            known = {f"{rtype}/{rid}" for rtype, rid in set_resources(name)}
            for _, resource in walk_resources(name):
                for reference in walk_references(resource):
                    if reference.startswith("urn:"):
                        continue
                    target = reference.split("/_history/")[0]
                    self.assertIn(
                        target,
                        known,
                        f"{resource['resourceType']}/{resource['id']} references missing {target}",
                    )

    def test_every_patient_has_one_primary_condition_and_encounter(self):
        for name in SETS:
            resources = set_resources(name)
            patients = {rid for rtype, rid in resources if rtype == "Patient"}
            conditions = [
                r for (rtype, _), r in resources.items()
                if rtype == "Condition" and r["subject"]["reference"].startswith("Patient/")
            ]
            encounters = [
                r for (rtype, _), r in resources.items()
                if rtype == "Encounter" and r["subject"]["reference"].startswith("Patient/")
            ]
            self.assertEqual(len(conditions), len(patients), name)
            self.assertEqual(len(encounters), len(patients), name)

    def test_patient_identifiers_carry_mrn_and_study_subject(self):
        for name in SETS:
            for (rtype, rid), resource in set_resources(name).items():
                if rtype != "Patient":
                    continue
                systems = {item["system"]: item["value"] for item in resource["identifier"]}
                self.assertIn(generate.CS["mrn"], systems)
                self.assertRegex(systems[generate.CS["mrn"]], r"^MRN-\d{2}-\d{5}$")
                self.assertEqual(systems[generate.CS["subject_id"]], rid)
                self.assertEqual(systems[generate.CS["study_no"]], generate.STUDY_ID)

    def test_gbm_condition_and_biomarker_codes(self):
        for name in SETS:
            for (rtype, rid), resource in set_resources(name).items():
                if rtype == "Condition" and rid.endswith("PRIMARY"):
                    text = json.dumps(resource)
                    if "GBM" in rid or "glioblastoma" in text.casefold():
                        codes = {c["code"] for c in resource["code"].get("coding", [])}
                        if "9440/3" in codes:
                            self.assertIn("393563007", codes, rid)
                if rtype == "Observation" and rid.endswith("-MGMT"):
                    self.assertEqual(resource["code"]["coding"][0]["code"], "88199-1")
                if rtype == "Observation" and rid.endswith("-KPS"):
                    self.assertEqual(resource["code"]["coding"][0]["code"], "89261-2")
                if rtype == "MedicationRequest":
                    codes = {c["code"] for c in resource["medicationCodeableConcept"].get("coding", [])}
                    self.assertIn("L01AX03", codes, rid)


class DocumentTests(unittest.TestCase):
    def test_documentreference_attachments_decode_and_match_source(self):
        documents = {
            doc["id"]: doc
            for doc in json.loads((REPO / "app/assets/data/documents.json").read_text(encoding="utf-8"))["documents"]
        }
        for name in SETS:
            for (rtype, rid), resource in set_resources(name).items():
                if rtype != "DocumentReference":
                    continue
                attachment = resource["content"][0]["attachment"]
                raw = base64.b64decode(attachment["data"])
                self.assertEqual(len(raw), attachment["size"], rid)
                self.assertEqual(
                    base64.b64encode(hashlib.sha1(raw).digest()).decode("ascii"),
                    attachment["hash"],
                    rid,
                )
                self.assertGreater(len(raw), 100, rid)
                self.assertEqual(resource["masterIdentifier"]["value"], rid)
                if name == "baseline":
                    source = (REPO / "app" / documents[rid]["assetPath"]).read_bytes()
                    self.assertEqual(raw, source, rid)

    def test_diagnostic_reports_reuse_the_document_text(self):
        for name in SETS:
            resources = set_resources(name)
            for (rtype, rid), resource in resources.items():
                if rtype != "DiagnosticReport":
                    continue
                doc_id = rid.removeprefix("DR-")
                document = resources[("DocumentReference", doc_id)]
                self.assertEqual(
                    resource["presentedForm"][0]["data"],
                    document["content"][0]["attachment"]["data"],
                    rid,
                )
                self.assertEqual(resource["subject"], document["subject"], rid)

    def test_every_baseline_document_has_a_reference(self):
        baseline = {rid for rtype, rid in set_resources("baseline") if rtype == "DocumentReference"}
        expected = {
            doc["id"]
            for doc in json.loads((REPO / "app/assets/data/documents.json").read_text(encoding="utf-8"))["documents"]
        }
        self.assertEqual(baseline, expected)

    def test_arrival_patients_are_new(self):
        baseline = {rid for rtype, rid in set_resources("baseline") if rtype == "Patient"}
        arrivals = {rid for rtype, rid in set_resources("arrivals") if rtype == "Patient"}
        h2_baseline = {rid for rtype, rid in set_resources("hospital2/baseline") if rtype == "Patient"}
        h2_arrivals = {rid for rtype, rid in set_resources("hospital2/arrivals") if rtype == "Patient"}
        self.assertEqual(len(arrivals), 3)
        self.assertTrue(arrivals.isdisjoint(baseline))
        self.assertEqual(len(h2_baseline), 5)
        self.assertEqual(len(h2_arrivals), 2)
        self.assertTrue(h2_baseline.isdisjoint(baseline | arrivals))
        self.assertTrue(h2_arrivals.isdisjoint(baseline | arrivals | h2_baseline))

    def test_hospital2_documents_are_dutch(self):
        for name in ("hospital2/baseline", "hospital2/arrivals"):
            for (rtype, rid), resource in set_resources(name).items():
                if rtype != "DocumentReference":
                    continue
                attachment = resource["content"][0]["attachment"]
                self.assertEqual(attachment["language"], "nl", rid)
                text = base64.b64decode(attachment["data"]).decode("utf-8")
                self.assertIn("SYNTHETISCH DOCUMENT", text, rid)


class GeneratorTests(unittest.TestCase):
    def test_committed_bundles_are_current(self):
        self.assertEqual(generate.main(["--check"]), 0)

    def test_generation_is_deterministic(self):
        first = generate.build()
        second = generate.build()
        self.assertEqual(first, second)

    def test_no_real_names_appear(self):
        surnames = set()
        for name in SETS:
            for (rtype, _), resource in set_resources(name).items():
                if rtype == "Patient":
                    for item in resource["name"]:
                        surnames.add(item["family"])
        self.assertEqual(surnames, {"Proefpersoon"})


@unittest.skipUnless(os.environ.get("FHIR_INTEGRATION") == "1", "set FHIR_INTEGRATION=1 to load into HAPI")
class IntegrationTests(unittest.TestCase):
    def test_load_baseline_and_arrivals_is_idempotent(self):
        import load

        base = os.environ.get("FHIR_BASE_URL", "http://127.0.0.1:8090/fhir")
        self.assertEqual(load.main(["--set", "all", "--base-url", base, "--quiet", "--check-counts"]), 0)
        self.assertEqual(load.main(["--set", "all", "--base-url", base, "--quiet", "--check-counts"]), 0)


if __name__ == "__main__":
    unittest.main()
