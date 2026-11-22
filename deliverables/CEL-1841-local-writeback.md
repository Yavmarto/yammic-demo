# Local trial write-back feasibility

Synthetic milestone only. Branch `cel-1841-writeback`, implementation commit `9cb80d5` (based on `73c0941`). The branch is the local handoff; no integration checkout or presentation stack was changed.

From `backend`, against a dedicated local Postgres database (the test resets its public schema):

```sh
TEST_DATABASE_URL='postgresql+psycopg://postgres:@/cel_1841_test?host=/Users/yoshimartodihardjo/.yamicc-pg' uv run pytest -q tests/test_writeback.py
```

Observed: **1 passed**, one Starlette/httpx deprecation warning. The test uses one synthetic participant at one site in fictional study GBM-NL-2026-01. It defers a seeded document extraction, confirms pending/deferred exclusion, corrects it through the existing nurse review path, and sends the verified KPS value to a receiver-owned mapping. SQLite is a separate persistent receiver boundary. The receiver commits before a simulated lost acknowledgement; retries retain one row under a stable delivery identity. The source document ID and document/extraction evidence link travel with the value. The existing hash-chained audit records failure and subsequent successful attempts and verifies cleanly. The same corrected value appears in an ODM 1.3.2 export validated against the bundled XSD. The adapter enforces the existing PI/monitor export roles; nurse is denied.

Limitations: This is a local callable adapter contract, not a deployed service or real EDC integration. The mapping covers one field only. The evidence link identifies the demo document and extraction; it is not a cross-system production deep-link contract. Retry is invoked by the caller, not scheduled. Reconciliation, concurrency/revocation handling and production security require further design. FR-063 policy remains unresolved; the demo role restriction is not a policy decision. No clinical or regulatory validation is claimed.
