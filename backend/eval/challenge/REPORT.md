# Local provider comparison: Dutch abstention and evidence

**Dataset:** 10 synthetic notes, 21 independently labelled field decisions, 7 expected abstentions. Labels were set before provider runs. The original cases and labels were not changed. No model or prompt tuning was done on this challenge set.

| Measure | Rules | Ollama |
|---|---:|---:|
| Correct decisions | 19/21 (0.905) | 17/21 (0.810) |
| Correct abstentions | 6/7 | 6/7 |
| Exact evidence span | 12/14 | 1/14 |
| Invalid source spans | 0 | 0 |
| Per-field precision/recall/F1 | See provider result | See provider result |

Rules missed one of two abstentions for extent of resection; Ollama proposed a subtotal resection for the hedged case. Both providers followed the expected abstention in four progression-date cases. Ollama chose the superseded methylated result in the conflicting MGMT case, missed one age, and abstained on the stated adverse-event grade. The zero invalid-span count means each proposed source span checked by the runner matched its source text; it does not mean the span was clinically sufficient. Exact-span agreement is strict string equality with the independently labelled evidence quote.

**Ollama:** `qwen2.5:7b-instruct` (local model digest `845dbda0ea48`), temperature 0, seed 42, timeout 240 seconds per document; 10/10 completed with no timeout. Rules used `rules-regex-v1` and ran offline. No reviewer time was measured.

Machine-readable results and per-field accuracy/F1, correct abstention counts and denominators are in [`results/rules/latest.json`](results/rules/latest.json) and [`results/ollama/latest.json`](results/ollama/latest.json). The challenge and runner are in this directory. The requested local `dev` base `22e65a7` was not present in this checkout; work started from available `dev` HEAD `bcc0f74`.

**Integrated dev check:** At commit `0f38068`, the rules run reproduced all decision, abstention and span results with a different prompt hash. The table preserves the original comparison from `bcc0f74`. This issue adds a separate Ollama rerun on integrated commit `8e4132f`; see the section below.

## Integrated rerun on `8e4132f`

The frozen challenge was rerun with both providers on commit `8e4132f7249ac71c52530070d6a0ac32f2427b28`. Both completed 10/10 documents without timeouts. Rules scored 19/21 decisions, 6/7 abstentions, 12/14 exact spans and 0 invalid spans; Ollama scored 17/21, 6/7, 1/14 and 0. Full hashes, timing, per-field results and run metadata are recorded in [`results/integrated-8e4132f/REPORT.md`](results/integrated-8e4132f/REPORT.md) and the provider JSON files. The earlier result files above remain unchanged.

## CEL-1857 — extraction accuracy and abstention (rerun)

The CEL-1856 tables above are unchanged. This section records the CEL-1857 rerun. The frozen denominators are unchanged: 21 decisions, 14 expected spans, 7 expected abstentions on the tuning set; 25 pairs, 17 expected spans, 4 expected abstentions on the holdout.

**Macro-F1.** The all-field value (frozen, 11 fields on the tuning set) is reported unchanged. The B4 value is the mean F1 over fields with at least one positive gold value, per the CEL-1857 CEO decision. Fields with no positive gold score F1 0.0 by convention and are excluded from the B4 value.

**Tuning set (`dutch-abstention-evidence-challenge-v1`, used for tuning):**

| Provider | Decisions | Abstentions | Exact spans | Invalid spans | Macro-F1 all 11 (frozen) | Macro-F1 positive-gold (B4) |
|---|---:|---:|---:|---:|---:|---:|
| Rules (`rules_v1`, this commit) | 21/21 | 7/7 | 14/14 | 0 | 0.909 | 1.000 |
| Ollama, `extract_v4` (CEL-1856, unchanged) | 17/21 | 6/7 | 1/14 | 0 | 0.742 | 0.817 |
| Ollama, `extract_v5` prompt only | 17/21 | 6/7 | 1/14 | 0 | 0.697 | 0.767 |
| Ollama, `extract_v5` prompt + quote trim | 17/21 | 6/7 | 5/14 | 0 | 0.697 | 0.767 |

The v4 Ollama row is computed from the committed CEL-1856 `results/ollama/latest.json`. The v5 rows are CEL-1857 runs. Quote trimming changed exact spans but not decisions or F1, because F1 scores the value.

**Abstention set (`eval/abstention_v2`, new, written before any run, used for tuning only):** 9 documents, 10 decisions, 8 expected abstentions, 2 positives. Rules before the CEL-1857 fixes: 6/10 decisions. Rules after the fixes: 10/10 decisions, 8/8 abstentions. Use this set as a regression fixture. It is not a held-out measure.

**Holdout (`independent_dutch`, not used for tuning, run once per provider):**

| Provider | Accuracy | Micro-F1 | Macro-F1 (all 15 fields = positive-gold) | Abstention recall | Exact spans | Invalid spans |
|---|---:|---:|---:|---:|---:|---:|
| Rules (`rules_v1@dbda93cfc6a7`) | 21/25 (0.84) | 0.9048 | 0.9222 | 2/4 (0.50) | 17/21 (0.81) | 0 |
| Ollama `extract_v5` | 22/25 (0.88) | 0.9333 | 0.9333 | 1/4 (0.25) | 7/24 (0.29) | 0 |

Rules holdout accuracy, micro-F1, macro-F1, abstention and exact spans are identical to the CEL-1856 baseline. Ollama has no prior holdout baseline: the committed benchmark deliverable records that the Ollama path "was not run". The Ollama holdout row is therefore a first run, not a matched comparison.

**D13 criteria status (rerun, not signed off by QA):**

- **B1 exact span:** tuning set rules 14/14. Holdout rules 17/21 (0.81), still PARTIAL. Holdout Ollama 7/24 (0.29), below the rules result.
- **B3 abstention:** tuning set rules 8/8 on the new abstention set. Holdout 2/4 (rules) and 1/4 (Ollama), both FAIL.
- **B4 macro-F1 ≥ 0.95:** holdout rules 0.9222 and Ollama 0.9333, both FAIL. The tuning-set positive-gold value of 1.000 is not evidence for B4, because that set was used for tuning.

The threshold wording for B1 and B3 is not in this checkout. The statuses above follow the CEO note on CEL-1857. QA must confirm them against the D13 text on CEL-1856.

**Scope limits and gaps:**

1. The holdout abstention misses (rules 2/4, Ollama 1/4) were not fixed. The rules changes were tuned on the new abstention set, and they did not transfer. The holdout was not read for tuning.
2. Ollama exact spans are still low (5/14 on the tuning set). The remaining mismatches include whole-sentence quotes and clause tails such as "volgens RANO". Clause tails are left to the prompt.
3. Ollama abstains on AGE, TMZPLNC and AEGRADE where gold has values on the tuning set. It proposes EXTRES on a case where gold abstains. Decisions stayed at 17/21 across v4 and v5.
4. The holdout macro-F1 on the B4 basis is computed from the existing per-field stats. The holdout evaluator itself does not emit it.
5. The `extract_v5` prompt is now the default Ollama prompt for the whole app. The v4 results remain recorded under their own version hash.
6. Synthetic, fictional data only. No external calls, no paid providers, no real data, no FR-063 change, no fallback persistence change.

**Test evidence:** `tests/test_ai_rules.py`, `test_ai_ollama.py`, `test_ai_eval.py`, `test_ai_service.py`: 31 passed. DB-backed API tests were not run, because they need `TEST_DATABASE_URL`.
