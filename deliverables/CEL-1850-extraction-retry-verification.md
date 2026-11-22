# Synthetic failed extraction retry verification

Baseline: local dev 5ab6bc3. Scope: synthetic data and local rules provider; no deployment or external provider.

- The review screen loads failed runs for the selected participant, displays a generic safe reason, permits nurse/PI retry, and shows queued/completed feedback. Monitor is read-only. Dismiss reveals another unresolved failure; reopening restores it.
- Retry locks the failed original and creates at most one linked child. Repeated and concurrent requests return the same child. The child keeps participant, document and provider scope; retry requests record the actor and both run IDs in the audit trail. A failed child can itself be retried.
- Isolated PostgreSQL database in the run scratch area: `pytest -q tests/test_run_retry.py` — 1 passed. Simulated provider failure, failed original retained, concurrent and repeat identity, monitor denial, document/participant scope, audit, rules-provider completion, and preservation of a previously reviewed KPS value were checked.
- `flutter test --no-pub test/run_retry_test.dart` — 2 passed. Failure reason, nurse retry and completed feedback, and monitor denial were checked using a mock backend.
- `flutter analyze --no-pub lib/features/review/review_screen.dart test/run_retry_test.dart` — no issues.
- The test PostgreSQL instance used a private Unix socket and dedicated scratch storage. The existing presentation stacks were not touched.
