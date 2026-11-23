# Local synthetic source-to-receiver integration

From the repository root, with Docker running and the locally cached `postgres:16` and `hapiproject/hapi:latest` images available:

```sh
cd backend
uv sync --group dev
PYTHONPATH=. uv run --no-sync python integration/local_workflow.py
```

The command creates uniquely named disposable Docker containers and a network, uses ephemeral loopback ports and a temporary receiver file, and removes them on exit. It requires resources for HAPI (up to 1 GiB heap) and may take several minutes on first boot. It uses no external API; Docker is explicitly instructed not to pull images. A port allocation race is possible if another process takes a selected port before the container binds it.

The application study, sites, form and demo users are seeded. Participant GBM-NL-001 and its documents are excluded from the application seed, then imported from the fictional HAPI bundle. The test requests rules extraction for DOC-001-DIS, uses the demo nurse API role to accept KPS 80, and uses the demo monitor role to preview and send twice to the in-process SQLite simulated receiver. It asserts the receiver's source, subject, site, extraction and evidence link, one stored delivery, and the same subject's KPS and extraction provenance in ODM validated against the bundled ODM 1.3.2 XSD. The review is an automated API action standing in for a human; it is not a usability test or a real human assessment.

This does not connect a hospital or vendor EDC, test real data, establish full CDISC conformance, or implement FR-063. The receiver is local simulation and supports only this participant and KPS field. Existing `tests/test_writeback_api.py::test_synthetic_api_retry_roles_and_unavailable` covers stale preview and a simulated lost acknowledgement; `tests/test_writeback.py::test_local_writeback_retry_and_odm` covers the same receiver identity and XSD path at service level. Those tests have their own isolated test-database setup; set `TEST_DATABASE_URL` to a disposable database because their fixture drops its public schema. No claim about those tests is made unless they are run separately.
