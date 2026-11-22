# D10 — AI architecture & evaluation plan (demo scope)

Issue: CEL-1741 (T14) · Owner: Applied Research Lead · Status: revised after QA fact-check (CEL-1817); re-QA pending
Scope: the YAMICC synthetic-data demo only. All data is synthetic. Cost, pricing, procurement and production rollout are out of scope.
Sources: 06 §3, 05 UI-005, `backend/app/ai/`, `backend/eval/`, `backend/eval/results/w4_report.md` (2026-11-21), `deliverables/demo_script.md`.

## 1. Recommendation

- Keep the **local open-weight model** (`qwen2.5:7b-instruct` through Ollama) as the live extractor in the demo. Keep the **deterministic `rules` provider** as the offline fallback. Both sit behind one provider interface.
- Make **human verification** the only route from an AI proposal to a verified eCRF value or an export. AI proposals are never exported.
- Measure every provider with the same gold set, span-integrity check and seeded hard cases. Report the numbers with the synthetic-data caveat.
- Confidence: **high** that the demo pipeline behaves as described. **Low** for any claim about clinical accuracy, because the gold set is synthetic.
- What would change this: a site dataset under approval, a materially different model, or a change to the demo's live-run requirement.

## 2. Architecture (as built)

| Component | What it does | Where |
|---|---|---|
| Run queue | Sync or the extract endpoint queues an `ai` run per participant or document | `backend/app/ai/routes.py` (`queue_provider_run`) |
| AI worker | Separate process `python -m app.ai`. Logs in as the `ai` service user and uses the REST API. It holds no database credentials | `backend/app/ai/service.py`, `client.py` |
| Providers | `rules`: offline, regex and terminology, about 10 ms per run. `ollama`: local model, JSON-schema constrained, temperature 0, seed 42 | `backend/app/ai/providers/` |
| Prompt registry | `extract_v1` to `extract_v4`, each with a SHA-256 tag. The tag is stored on every run | `backend/app/ai/registry.py`, `prompts/` |
| Span check | Every evidence quote is re-located in the source text. The API rejects a span that does not match with HTTP 422 | `backend/app/ai/span.py`; `backend/app/routes.py:420` |
| Review (UI-005) | Three columns: source with highlighted evidence, proposals, target eCRF field. Actions: Accept, Correct, Defer, Reject | `app/lib/features/review/` |
| Audit | Each run, proposal and human decision is appended to a hash chain. `/audit/verify` checks it | `backend/app/routes.py:325` |
| Export | Only verified values leave the platform (CDISC ODM, FHIR QuestionnaireResponse with Provenance) | `backend/app/export/` |

### Demo workflow

1. Sync sends new FHIR documents into the backend. Each document queues an extraction run.
2. The worker runs the queue one document at a time, using Ollama when it is available.
3. Each proposal carries an evidence span, a confidence, the provider, the model id and the prompt version.
4. A nurse or PI decides each proposal in the review screen. The decision is written to the audit chain.
5. The audit view verifies the chain. Export includes verified values only.

## 3. Model and provider choice (demo)

| | `rules` | `ollama` (`qwen2.5:7b-instruct`) |
|---|---|---|
| Role | Fallback and deterministic baseline | Live extractor in the demo |
| Runs | Local, no network | Local, through Ollama on `localhost:11434` |
| Time per document | < 10 ms (17 ms for all 13 documents) | 12.2–45.1 s per document in the committed eval (13 runs; mean 38 s; 34–45 s excluding the short DOC-005-MRI) |
| Data leaves the machine | No | No |
| Measured quality (synthetic gold set) | F1 1.000 | F1 1.000 |

Why local: the demo claims that no data leaves the laptop and that no paid API is used. Both are true today. A hosted-API comparison is not part of this demo plan.

Not evaluated for the demo: hosted EU API models, other open-weight models, and any cost or pricing comparison. These belong to a later decision by the CTO, not to this plan.

## 4. Human verification

- **Accept** is disabled on an abstained proposal. The API returns 422 if a client tries it anyway (`backend/app/routes.py:210`).
- **Correct** requires a corrected value. **Reject** requires a reason. The API enforces both (`routes.py:206–208`).
- **Defer** keeps the field open as a task. It is not a silent gap.
- Confidence caps are applied before a proposal reaches the reviewer:
  - hedged wording (for example "probably", "waarschijnlijk") caps confidence at **0.45** when the model's confidence is 0.6 or higher (`backend/app/ai/providers/ollama.py:228–230`). The `rules` provider gives the same 0.45 on the same hard case;
  - a value that the quote does not support caps confidence at **0.35** (`ollama.py:232–234`).
- Each decision records the actor, the role, the time, the before and after values, and the model and prompt that proposed the value.
- The Monitor role is read-only in the demo.

## 5. Fallback behaviour

| Trigger | What happens | Visible to the user |
|---|---|---|
| Ollama not reachable, or the model is not pulled, at run start | Run uses `rules` from the start | Run provider `rules`; warning recorded; `fallbackFrom = ollama` |
| Ollama fails during a run (timeout is 240 s per call) | Documents not yet processed are re-run with `rules`. Proposals already posted are kept and not duplicated | Warning recorded; provider changes to `rules` for the remaining documents |
| `rules` fails | Run is marked `failed` with the error. There is no further fallback | Run shows failed; no proposals are posted. Not yet tested (open item 2) |
| Quote not found in the source | Proposal becomes an abstention with `evidence_not_found` | Accept disabled; "No evidence span" in the source pane |

Demo line for a slow queue: the local model was slow, so the deterministic extractor took over; the review loop is the same.

## 6. Evaluation plan

Metrics, per field and per provider:

- precision, recall, F1 and macro-F1 against the gold set;
- abstention rate and mean confidence;
- span errors (any proposed span that does not match the source fails the run);
- hard-case pass (seeded wrong value, low confidence, abstention, arrivals abstention);
- run time per document.

Gold set: 13 documents, 57 annotations, generated with the synthetic data. The three DOC-005 documents are part of this 13-document set. The live arrival check (AC-5) is a separate API run for participant GBM-NL-005, not a held-out set.

Regression rule: rerun the eval on any change to a prompt, a model or a provider. Compare the new per-field table with the committed `latest-*.json`.

### Measured results (committed eval output, 2026-11-21)

| Provider | Precision | Recall | F1 | Abstention | Span errors | Hard cases | Live arrivals gold checks |
|---|---:|---:|---:|---:|---:|---|---:|
| rules (`rules_v1`) | 1.000 | 1.000 | 1.000 | 0.066 | 0 | 4 of 4 pass | 15 of 15 |
| ollama (`extract_v4`) | 1.000 | 1.000 | 1.000 | 0.066 | 0 | 4 of 4 pass | 15 of 15 |

**Caveat.** The gold labels come from the same generator that produced the demo data. A score of 1.000 shows that the pipeline is consistent end to end. It does not show clinical accuracy. Real evaluation needs site data under approval, which is out of scope here.

## 7. Demo acceptance checks

Pass criteria for the demo. Status shows whether the check is already measured or still has to be run.

| ID | Check | Pass criterion | Status |
|---|---|---|---|
| AC-1 | Span integrity | 0 span errors on the 13-document set, both providers | Measured (W4) |
| AC-2 | Gold-set quality | Macro-F1 ≥ 0.95 on the 13-document set, both providers | Measured: 1.000 (synthetic caveat applies) |
| AC-3 | Hard cases | 4 of 4 seeded cases pass, both providers | Measured (W4) |
| AC-4 | Abstention | PROGDAT is abstained with confidence 0.0 on DOC-003-MRI and DOC-005-MRI; Accept is disabled | Measured (W4) |
| AC-5 | Live arrivals | `POST /participants/GBM-NL-005/extract?provider=ollama` completes with 15 of 15 gold checks | Measured (W4) |
| AC-6 | Human gate | Accept on an abstained extraction returns 422; Correct without a value returns 422 | Code-verified; API run pending |
| AC-7 | Fallback | With Ollama stopped, a run completes with provider `rules`, `fallbackFrom = ollama`, and a warning in the run record | Pending |
| AC-8 | Audit | After one run and one decision, `/audit/verify` returns `ok: true` | Measured once (W4, count 145); repeat pending |
| AC-9 | Timing | Each Ollama document completes within 66 s (budget from the demo script; measured maximum 45.1 s in the W4 eval); the arrivals queue finishes within 6 min | Per-document measured (max 45.1 s, W4 eval). Queue time 323 s is script-reported, not in the committed eval. Repeat pending |
| AC-10 | Export excludes AI | An export contains verified values only; no unverified proposal appears | Pending |

## 8. Open items for QA

1. **Two confidence values for the same hedged case.** The live engine (code cap and committed eval, `latest-rules.md`, `latest-ollama.md`, `w4_report.md`) gives **0.45**. The seeded demo record EXT-0022 in `app/assets/data/extractions.json` gives **0.38**, and `backend/eval/gold.py` copies that 0.38 into the eval output as gold metadata. `deliverables/demo_script.md:289` quotes 0.38. Decision needed: either regenerate the seeded record (`app/tool/generate_demo_data.py`, Engineering-owned) to 0.45, or keep 0.38 and say in the script that it is the seeded value. This plan does not change either file.
2. **Pending checks.** AC-6 (API run), AC-7, AC-10, the `rules` failure row in §5, and the repeat runs for AC-8 and AC-9 have not been executed.
3. **Timing figures in the demo script are not measured.** `demo_script.md:226` says "35–66 s per document", and `demo_script.md:534` says "mean ≈45 s". The committed eval gives 12.2–45.1 s and a mean of 38 s. The 323 s queue time is script-reported only.
4. **Script claim not re-measured.** The script says the live GBM-NL-009 pathology run produces "nine abstentions". The committed eval shows 9 abstentions on DOC-005-PATH, the same pattern. This plan has not re-run GBM-NL-009.

## 9. Out of scope

Cost estimates, pricing, procurement, hosted-model comparison, production rollout, clinical validation, and regulatory classification (T15 / D11). Real patient data is not used.
