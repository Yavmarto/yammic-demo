"""FHIR read side: a tiny stdlib HTTP client. Tests swap it for `BundleSource` (no network)."""
import json
import os
import urllib.parse
import urllib.request
from urllib.error import URLError

BASE = os.environ.get("FHIR_BASE_URL", "http://localhost:8090/fhir").rstrip("/")
# Sync order matters: Patient first so participants exist before their facts.
TYPES = ("Patient", "Condition", "Observation", "Procedure", "MedicationRequest",
         "MedicationStatement", "MedicationAdministration", "Medication",
         "DocumentReference", "DiagnosticReport")


class FhirError(Exception):
    pass


def _get(url: str, timeout: float = 15):
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/fhir+json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except (URLError, OSError, ValueError) as e:
        raise FhirError(f"{url.split('?')[0]}: {e}") from e


class HttpSource:
    def __init__(self, base: str = BASE):
        self.base = base.rstrip("/")

    def metadata(self) -> dict:
        m = _get(f"{self.base}/metadata?_summary=true", timeout=5)
        return {"fhirVersion": m.get("fhirVersion"),
                "software": (m.get("software") or {}).get("name"),
                "softwareVersion": (m.get("software") or {}).get("version")}

    def search(self, rtype: str, since: str | None = None) -> list[dict]:
        q = {"_count": "200", "_sort": "_lastUpdated"}
        if since:
            q["_lastUpdated"] = f"gt{since}"
        url, out = f"{self.base}/{rtype}?{urllib.parse.urlencode(q)}", []
        while url:
            b = _get(url)
            out += [e["resource"] for e in b.get("entry", []) if e.get("resource", {}).get("resourceType") == rtype]
            url = next((link["url"] for link in b.get("link", []) if link["relation"] == "next"), None)
            if url:  # HAPI builds next links against the bare host, drop its path and re-root on our base
                url = f"{self.base}?{urllib.parse.urlparse(url).query}"
        return out

    def transaction(self, bundle: dict) -> dict:
        req = urllib.request.Request(self.base, data=json.dumps(bundle).encode(), method="POST",
                                     headers={"Content-Type": "application/fhir+json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            raise FhirError(f"transaction: {e.code} {e.read()[:500]!r}") from e
        except (URLError, OSError) as e:
            raise FhirError(str(e)) from e

    def validate(self, resource: dict) -> dict:
        data = json.dumps(resource).encode()
        req = urllib.request.Request(f"{self.base}/{resource['resourceType']}/$validate", data=data, method="POST",
                                     headers={"Content-Type": "application/fhir+json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:  # HAPI answers 412 with the OperationOutcome
            return json.loads(e.read())


class BundleSource:
    """Offline stand-in: serves resources from in-memory lists (used by tests)."""

    def __init__(self, resources: list[dict], stamp: str = "2026-11-21T12:00:00.000+00:00"):
        self.res = [dict(r, meta={**r.get("meta", {}), "lastUpdated": r.get("meta", {}).get("lastUpdated", stamp)})
                    for r in resources]

    def metadata(self) -> dict:
        return {"fhirVersion": "4.0.1", "software": "in-memory", "softwareVersion": "test"}

    def search(self, rtype, since=None):
        return [r for r in self.res if r["resourceType"] == rtype
                and (not since or r["meta"]["lastUpdated"] > since)]
