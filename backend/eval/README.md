# AI extraction eval (W4)

Gold-label evaluation for the `rules` and `ollama` providers.

```bash
cd backend
uv run python -m eval.run_eval --provider rules          # fast, offline
uv run python -m eval.run_eval --provider ollama         # local model, ~45 s/document
uv run python -m eval.run_eval --provider rules --provider ollama
uv run python -m eval.run_eval --dataset arrivals        # held-out new-arrivals set
```

Results are written to `backend/eval/results/`:

- `latest-<provider>.json` / `.md` — machine-readable and the table shown by `GET /ai/eval`
- `<provider>-<timestamp>.json` — kept history
- `latest.json` / `latest.md` — the most recent run of any provider

## What is scored

- Gold labels come from the synthetic generator (`app/assets/data/extractions.json`).
  The seeded "wrong value" case is scored against its stated expected correction,
  not the deliberately wrong proposal. Seeded abstentions stay abstentions.
- A held-out `fixtures/arrivals/` set (3 documents for `GBM-NL-005`) is included in
  `--dataset all` and can be evaluated alone.
- Per field: precision, recall, F1, abstention rate, mean confidence, support.
- Span integrity: every proposed evidence span is checked against the source text;
  any mismatch fails the run (`spanErrors`).
- Seeded hard cases: wrong value, low confidence, abstention (plus the arrivals
  abstention). `hardCases.allPass` must be true in CI.

## Make targets (for DevOps to add to the root Makefile)

```make
eval:            ## gold-label eval for the offline provider
	cd backend && uv run python -m eval.run_eval --provider rules

eval-ollama:     ## gold-label eval for the local model
	cd backend && uv run python -m eval.run_eval --provider ollama

ai:              ## run the AI service loop (separate process)
	cd backend && uv run python -m app.ai --provider auto

ai-check:        ## provider + prompt registry status
	cd backend && uv run python -m app.ai --check
```

## Live new-arrivals check (until W3/W5 ingestion lands)

```bash
cd backend
uv run python -m eval.install_arrivals       # insert DOC-005-* for GBM-NL-005
curl -s -X POST 'localhost:8000/participants/GBM-NL-005/extract?provider=rules' \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{}'
uv run python -m app.ai --provider rules --once
curl -s localhost:8000/ai/eval -H "Authorization: Bearer $TOKEN"
```
