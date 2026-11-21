# W4 AI extraction — eval report (CEL-1777)

All data is synthetic. No paid API was used. Local-only run on this Mac.

## Environment and timings

- Mac: Apple M2 Pro, 10 cores, 16 GB; metal acceleration via Ollama 0.40.17.
- Model: `qwen2.5:7b-instruct` (Q4_K_M, 4.7 GB); generation ~27 tok/s.
- Per-document extraction time (13 docs): rules **17 ms total**, Ollama **493.9 s total** (38.0 s/document average; short MRI reports are faster).
- Live new-arrivals run (3 docs): rules **0.1 s**, Ollama **90.0 s** (39.3 s discharge, 11.6 s MRI, 38.6 s pathology).
- Prompt registry: rules `rules_v1@31d138e3eea9`; Ollama `extract_v4@1ef2060c673d` (four versions kept; hash recorded per run).

## Rules provider (deterministic, always offline)

Dataset: all, 13 documents. Precision **1.000**, recall **1.000**, F1 **1.000**, span errors **0**.

| Field | Support | Precision | Recall | F1 | Abstention rate | Mean confidence |
|---|---:|---:|---:|---:|---:|---:|
| SUBJID | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.990 |
| SITEID | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.980 |
| SEX | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.990 |
| AGE | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.970 |
| MHSTDAT | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.920 |
| HISTOLOGY | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.970 |
| IDHSTAT | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.960 |
| MGMTPROM | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.930 |
| KPS | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.900 |
| EXTRES | 5 | 1.000 | 1.000 | 1.000 | 0.000 | 0.810 |
| RTDOSE | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.960 |
| RTFRAC | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.960 |
| TMZPLNC | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.890 |
| AEGRADE | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.830 |
| PROGDAT | 4 | — | — | — | 1.000 | — |

- wrongValue: PASS — DOC-002-PATH / MGMTPROM; expected unmethylated, got proposed Unmethylated (confidence 0.93)
- lowConfidence: PASS — DOC-002-MRI / EXTRES; expected confidence < 0.6, got proposed Subtotal resection (confidence 0.45)
- abstention: PASS — DOC-003-MRI / PROGDAT; expected abstained, got abstained Not stated (confidence 0.0)
- arrivalsAbstention: PASS — DOC-005-MRI / PROGDAT; expected abstained, got abstained Not stated (confidence 0.0)

## Ollama provider (local `qwen2.5:7b-instruct`, JSON-schema constrained)

Dataset: all, 13 documents. Precision **1.000**, recall **1.000**, F1 **1.000**, span errors **0**.

| Field | Support | Precision | Recall | F1 | Abstention rate | Mean confidence |
|---|---:|---:|---:|---:|---:|---:|
| SUBJID | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.950 |
| SITEID | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.950 |
| SEX | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.958 |
| AGE | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.958 |
| MHSTDAT | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.950 |
| HISTOLOGY | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.950 |
| IDHSTAT | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.950 |
| MGMTPROM | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.950 |
| KPS | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.958 |
| EXTRES | 5 | 1.000 | 1.000 | 1.000 | 0.000 | 0.840 |
| RTDOSE | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.958 |
| RTFRAC | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.958 |
| TMZPLNC | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.958 |
| AEGRADE | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.958 |
| PROGDAT | 4 | — | — | — | 1.000 | — |

- wrongValue: PASS — DOC-002-PATH / MGMTPROM; expected unmethylated, got proposed Unmethylated (confidence 0.95)
- lowConfidence: PASS — DOC-002-MRI / EXTRES; expected confidence < 0.6, got proposed Subtotal resection (confidence 0.45)
- abstention: PASS — DOC-003-MRI / PROGDAT; expected abstained, got abstained Not stated (confidence 0.0)
- arrivalsAbstention: PASS — DOC-005-MRI / PROGDAT; expected abstained, got abstained Not stated (confidence 0.0)

Every proposed evidence quote was re-located in the source text. The service abstains
when a quote is not found and caps confidence for hedged wording. Ollama proposals with
a garbled/empty value are re-read from the verified quote (e.g. IDH `R132H negative`
→ `IDH-wildtype`); this never invents a span.

## Live API check (new arrivals, both providers)

- Fixture: `backend/eval/fixtures/arrivals/` (DOC-005-PATH / DOC-005-MRI / DOC-005-DIS for GBM-NL-005), inserted with `python -m eval.install_arrivals` until W3/W5 ingestion lands.
- `POST /participants/GBM-NL-005/extract?provider=rules` → run 11 completed, 45 proposals (20 proposed / 25 abstained), prompt `rules_v1@31d138e3eea9`.
- `POST /participants/GBM-NL-005/extract?provider=ollama` → run 12 completed, 45 proposals (22 proposed / 23 abstained), prompt `extract_v4@1ef2060c673d`.
- Gold checks through `GET /participants/GBM-NL-005/extractions`: **15/15 per provider** (the arrivals gold covers only the fields present in each document).
- Audit chain after both runs: `GET /audit/verify` → `ok: true`, count 145. Run events are `run.created` (human/nurse), `run.running` and `run.completed` (ai/service); each proposal writes `extraction.proposed`.
- Eval is served by `GET /ai/eval` (per-provider latest files) and shown by the app.

## Endpoints added

- `GET /ai/providers` — availability, model, paid flag (`claude` disabled by Gate 3).
- `GET /ai/prompts` — prompt versions + SHA-256, active version.
- `GET /ai/runs` — run list under the AI namespace.
- `GET /ai/eval?provider=` — latest eval result (all providers included).
- `POST /participants/{pid}/extract?provider=rules|ollama|auto` — queue a run with the requested provider recorded; the AI service consumes it from `GET /runs?status=queued`.

Existing contract routes (`POST /participants/{pid}/extraction-runs`, `PATCH /runs/{rid}`,
`POST /runs/{rid}/extractions`, `GET /runs/{rid}/events`) are unchanged.

## Service

`python -m app.ai --provider auto` polls queued runs, reads documents and eCRF fields
through the API as the `ai` service user, posts proposals, and logs one JSON line per
run/document (provider, model, prompt hash, duration, counts, warnings). No DB
credentials. If Ollama is down or fails mid-run it falls back to `rules` and records
`fallbackFrom`.

## Tests

`cd backend && uv run pytest` → **28 passed**. AI tests cover: span integrity on every
proposal, gold values, abstention, evidence-not-found → abstain, empty/garbled value
recovery from a verified quote, API queue/ingest flow, and Ollama-down / mid-run
fallback to rules.

## Open

- DevOps: add the `make eval`, `make eval-ollama`, `make ai`, `make ai-check` targets
  from `backend/eval/README.md` to the root Makefile.
- The live demo host must run `ollama serve` and have `qwen2.5:7b-instruct` pulled;
  `auto` falls back to rules if not.
- W3/W5 ingestion replaces `eval.install_arrivals` for real "new arrivals" flow.
- `claude` remains a disabled stub gated on a Board decision (Gate 3).
