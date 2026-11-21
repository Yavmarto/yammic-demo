#!/usr/bin/env python3
"""Load the synthetic Yammic FHIR R4 bundles into a local HAPI FHIR server.

Stdlib only (no third-party packages). Every bundle entry is a transaction PUT
with a client-assigned id, so running the loader again updates the same
resources instead of duplicating them. When the server advertises `$validate`,
each resource is validated and the issues are printed.

Usage:
    python3 fhir-seed/load.py                       # load the baseline set
    python3 fhir-seed/load.py --set arrivals        # the live-sync arrivals
    python3 fhir-seed/load.py --set all             # both sets
    python3 fhir-seed/load.py --dry-run             # show the plan only
    python3 fhir-seed/load.py --no-validate         # skip $validate
    python3 fhir-seed/load.py --check-counts        # fail if totals differ

Exit codes:
    0  loaded and (with --strict-validate) validated without errors
    1  connection or load failure
    2  $validate reported errors and --strict-validate was set
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
from typing import Any

SEED_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_BASE = os.environ.get("FHIR_BASE_URL", "http://127.0.0.1:8090/fhir")
SETS = ("baseline", "arrivals")


class LoadError(RuntimeError):
    pass


class Client:
    def __init__(self, base_url: str, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self, method: str, path: str, body: Any | None = None) -> tuple[int, dict[str, Any]]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        data = None
        headers = {"Accept": "application/fhir+json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/fhir+json"
        last_error: Exception | None = None
        for attempt in range(3):
            request = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read()
                    status = response.status
            except urllib.error.HTTPError as error:
                raw = error.read()
                status = error.code
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                last_error = error
                time.sleep(1.0 + attempt)
                continue
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                payload = {"raw": raw.decode("utf-8", "replace")[:2000]}
            if status >= 500 and attempt < 2:
                time.sleep(1.0 + attempt)
                continue
            return status, payload
        raise LoadError(f"{method} {url} failed after 3 attempts: {last_error}")

    def wait_ready(self, timeout: float = 120.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        last: str = "no response"
        while time.monotonic() < deadline:
            try:
                status, payload = self.request("GET", "metadata")
                if status == 200 and payload.get("resourceType") == "CapabilityStatement":
                    return payload
                last = f"HTTP {status}"
            except LoadError as error:
                last = str(error)
            time.sleep(2.0)
        raise LoadError(
            f"FHIR server at {self.base_url} is not ready after {int(timeout)}s ({last}). "
            "Start it with: make up"
        )


def operation_outcome_errors(payload: dict[str, Any]) -> list[str]:
    issues = payload.get("issue", []) if isinstance(payload, dict) else []
    errors = []
    for issue in issues:
        severity = issue.get("severity")
        if severity in ("error", "fatal"):
            diagnostics = issue.get("diagnostics") or issue.get("details", {}).get("text") or ""
            errors.append(f"{severity}: {diagnostics}")
    return errors


def supports_validate(capability: dict[str, Any], resource_type: str) -> bool:
    for rest in capability.get("rest", []):
        for resource in rest.get("resource", []):
            if resource.get("type") != resource_type:
                continue
            for operation in resource.get("operation", []):
                if operation.get("name") == "validate":
                    return True
    return False


def load_manifest(name: str) -> dict[str, Any]:
    path = SEED_DIR / name / "manifest.json"
    if not path.exists():
        raise LoadError(
            f"{path} is missing. Run: python3 fhir-seed/generate.py"
        )
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def plan_files(sets: list[str]) -> tuple[list[str], list[dict[str, Any]]]:
    """Return ordered, de-duplicated bundle files and the manifests that define them."""
    seen: set[str] = set()
    ordered: list[str] = []
    manifests = []
    for name in sets:
        manifest = load_manifest(name)
        manifests.append(manifest)
        for relative in manifest["order"]:
            if relative in seen:
                continue
            seen.add(relative)
            ordered.append(relative)
    return ordered, manifests


def read_bundle(relative: str) -> dict[str, Any]:
    with (SEED_DIR / relative).open(encoding="utf-8") as handle:
        return json.load(handle)


def expected_counts(files: list[str]) -> dict[str, int]:
    # De-duplicate by (type, id): shared CodeSystems and Organizations appear in
    # both the baseline and the arrivals manifests.
    seen: set[tuple[str, str]] = set()
    counts: dict[str, int] = {}
    for relative in files:
        bundle = read_bundle(relative)
        for entry in bundle["entry"]:
            resource = entry["resource"]
            key = (resource["resourceType"], resource.get("id", ""))
            if key in seen:
                continue
            seen.add(key)
            counts[key[0]] = counts.get(key[0], 0) + 1
    return dict(sorted(counts.items()))


def post_bundle(client: Client, relative: str) -> tuple[int, int]:
    bundle = read_bundle(relative)
    expected = len(bundle["entry"])
    status, payload = client.request("POST", "", bundle)
    if status not in (200, 201):
        errors = operation_outcome_errors(payload)
        detail = "\n  ".join(errors[:8]) or json.dumps(payload)[:1500]
        raise LoadError(f"{relative}: HTTP {status}\n  {detail}")
    if payload.get("resourceType") != "Bundle":
        raise LoadError(f"{relative}: unexpected response {payload.get('resourceType')!r}")
    entries = payload.get("entry", [])
    if len(entries) != expected:
        raise LoadError(f"{relative}: sent {expected} entries, server returned {len(entries)}")
    created = updated = 0
    for entry in entries:
        code = str(entry.get("response", {}).get("status", ""))
        if code.startswith("201"):
            created += 1
        elif code.startswith("200"):
            updated += 1
        else:
            raise LoadError(f"{relative}: entry {entry.get('response', {}).get('location')} returned {code!r}")
    return created, updated


def validate_resources(client: Client, files: list[str], capability: dict[str, Any]) -> tuple[int, int]:
    checked = 0
    failed = 0
    for relative in files:
        bundle = read_bundle(relative)
        for entry in bundle["entry"]:
            resource = entry["resource"]
            resource_type = resource["resourceType"]
            if not supports_validate(capability, resource_type):
                continue
            path = f"{resource_type}/$validate"
            status, payload = client.request("POST", path, resource)
            checked += 1
            if status not in (200, 201):
                failed += 1
                errors = operation_outcome_errors(payload)
                detail = "\n    ".join(errors[:4]) or f"HTTP {status}"
                print(f"  [FAIL] {resource_type}/{resource['id']}\n    {detail}")
                continue
            errors = operation_outcome_errors(payload)
            if errors:
                failed += 1
                print(f"  [FAIL] {resource_type}/{resource['id']}")
                for error in errors[:4]:
                    print(f"    {error}")
    return checked, failed


def server_counts(client: Client, types: list[str], expected: dict[str, int] | None = None,
                  attempts: int = 20) -> dict[str, int]:
    # HAPI updates the search-count index asynchronously, so totals right after a
    # write can lag for a few seconds. Retry while a total is still below the
    # expected count (deleted resources can make it higher, so only wait on low).
    counts: dict[str, int] = {}
    for attempt in range(attempts):
        counts = {}
        pending = False
        for resource_type in types:
            path = f"{resource_type}/?_summary=count&_total=accurate"
            status, payload = client.request("GET", path)
            if status == 200:
                counts[resource_type] = payload.get("total", 0)
            else:
                counts[resource_type] = -1
            if expected and counts[resource_type] < expected.get(resource_type, 0):
                pending = True
        if not pending:
            break
        time.sleep(1.0)
    return counts


def print_counts(expected: dict[str, int], actual: dict[str, int]) -> None:
    print("  resource type            expected  on server")
    for resource_type in sorted(expected):
        server = actual.get(resource_type)
        server_text = "?" if server is None else ("error" if server < 0 else str(server))
        print(f"  {resource_type:24s} {expected[resource_type]:8d}  {server_text:>9s}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load synthetic FHIR R4 bundles into HAPI FHIR.")
    parser.add_argument("--set", dest="sets", default="baseline", choices=("baseline", "arrivals", "all"))
    parser.add_argument("--base-url", default=DEFAULT_BASE, help=f"FHIR base URL (default: {DEFAULT_BASE})")
    parser.add_argument("--timeout", type=float, default=60.0, help="per-request timeout in seconds")
    parser.add_argument("--dry-run", action="store_true", help="print the plan, do not touch the server")
    parser.add_argument("--no-validate", action="store_true", help="skip $validate")
    parser.add_argument("--strict-validate", action="store_true", help="exit 2 if $validate reports any error")
    parser.add_argument("--check-counts", action="store_true", help="exit 1 if server totals differ from the bundles")
    parser.add_argument("--quiet", action="store_true", help="only print the final summary")
    args = parser.parse_args(argv)

    sets = list(SETS) if args.sets == "all" else [args.sets]
    try:
        files, manifests = plan_files(sets)
    except LoadError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    expected = expected_counts(files)
    total = sum(expected.values())

    print(f"FHIR seed: set={args.sets} files={len(files)} resources={total} base={args.base_url}")
    if not args.quiet:
        for relative in files:
            bundle = read_bundle(relative)
            print(f"  {relative:42s} {len(bundle['entry']):3d} resources")

    if args.dry_run:
        for resource_type, count in expected.items():
            print(f"  {resource_type:24s} {count:5d}")
        return 0

    client = Client(args.base_url, timeout=args.timeout)
    try:
        capability = client.wait_ready()
    except LoadError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    started = time.monotonic()
    created_total = updated_total = posted_total = 0
    try:
        for relative in files:
            created, updated = post_bundle(client, relative)
            created_total += created
            updated_total += updated
            posted_total += len(read_bundle(relative)["entry"])
            if not args.quiet:
                print(f"  loaded {relative:42s} created={created:3d} updated={updated:3d}")
    except LoadError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    elapsed = time.monotonic() - started

    failed = 0
    checked = 0
    if not args.no_validate:
        print("Validating resources with $validate (server advertises it per resource type)...")
        checked, failed = validate_resources(client, files, capability)
        if checked == 0:
            print("  $validate not advertised by this server; skipped")
        else:
            print(f"  validated {checked} resources, {failed} with errors")

    actual = server_counts(client, list(expected), expected)
    print("")
    print(f"FHIR seed OK: {posted_total} bundle entries sent ({total} unique resources; "
          f"created {created_total}, updated {updated_total}) in {elapsed:.1f}s")
    print(f"DocumentReference on server: {actual.get('DocumentReference', '?')} "
          f"(expected {expected.get('DocumentReference', 0)} for set {args.sets})")
    if not args.quiet:
        print_counts(expected, actual)
    print("")

    if args.check_counts:
        mismatched = {
            key: (expected[key], actual.get(key))
            for key in expected
            if actual.get(key) != expected[key]
        }
        if mismatched:
            print("ERROR: server counts differ from the bundles:")
            for key, (want, got) in mismatched.items():
                print(f"  {key}: bundle={want} server={got}")
            return 1
    if args.strict_validate and failed:
        print("ERROR: $validate reported errors (see above)")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
