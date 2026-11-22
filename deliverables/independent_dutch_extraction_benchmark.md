# Independent Dutch synthetic extraction benchmark

**Status:** local, reproducible prototype benchmark. All passages and identifiers are fictional.

## Dataset and method

Five Dutch oncology report passages were authored for this benchmark, separate from the existing synthetic generator and fixtures. Before running a provider, the reference file recorded each target value, its exact literal evidence span, and fields that must be left absent. The labels are stored separately from the provider input. The set includes conflicting IDH findings, uncertain resection wording, explicit absence of a diagnosis date, and a dated progression statement.

Run the offline rules provider from `backend/`:

```sh
uv run python eval/independent_dutch/evaluate.py --provider rules
```

The script invokes the existing local provider interface and reads `gold.json` only after all extraction calls. It writes a machine-readable result to `backend/eval/results/independent_dutch/latest-rules.json`. No services, database, network model, or paid provider are needed. The optional Ollama path is supported with `--provider ollama` when a local model is installed; it was not run for this result.

## Rules provider result

There are **5 documents and 25 labeled document-field pairs** across 15 fields. The rules provider got **21/25 (84%)** status-and-value decisions correct, including **2/4 expected abstentions (50% abstention recall)**. For proposed values, micro precision, recall, and F1 were **0.9048**; macro field F1 was **0.9222**. It returned **21 proposals**; **17/21 (81.0%)** had the exact reference evidence span. It had **0 source-integrity errors**: every returned evidence span was present in the source text. The difference between exact-span agreement and integrity is that a real but broader or otherwise non-reference span can still be source-valid.

| Field | Labeled pairs | Accuracy | F1 | Exact reference span / proposals | Correct abstentions / expected |
|---|---:|---:|---:|---:|---:|
| AEGRADE | 1 | 1.00 | 1.00 | 1/1 | — |
| AGE | 1 | 1.00 | 1.00 | 1/1 | — |
| EXTRES | 2 | 0.50 | 0.67 | 1/2 | 0/1 |
| HISTOLOGY | 2 | 1.00 | 1.00 | 2/2 | — |
| IDHSTAT | 2 | 0.50 | 0.67 | 0/2 | 0/1 |
| KPS | 1 | 1.00 | 1.00 | 1/1 | — |
| MGMTPROM | 2 | 1.00 | 1.00 | 2/2 | — |
| MHSTDAT | 2 | 1.00 | 1.00 | 0/1 | 1/1 |
| PROGDAT | 2 | 1.00 | 1.00 | 1/1 | 1/1 |
| RTDOSE | 1 | 1.00 | 1.00 | 1/1 | — |
| RTFRAC | 1 | 1.00 | 1.00 | 1/1 | — |
| SEX | 1 | 1.00 | 1.00 | 1/1 | — |
| SITEID | 3 | 0.33 | 0.50 | 1/1 | — |
| SUBJID | 3 | 1.00 | 1.00 | 3/3 | — |
| TMZPLNC | 1 | 1.00 | 1.00 | 1/1 | — |

Field F1 scores proposed-value extraction only. Accuracy counts a correct explicit abstention as correct. Span counts are exact literal reference-span matches among provider proposals; absent gold evidence has no expected span.

## Manual entry versus assisted review protocol

Use the same five passages and the same field definitions in two rounds:

1. In the manual round, the reviewer enters values and marks fields unknown from the source, without AI proposals.
2. In the assisted round, the reviewer sees provider proposals and source highlights, then accepts, edits, rejects, or leaves each item unknown.
3. Use the same trained reviewers in both rounds. Counterbalance which round comes first across reviewers. Do not show gold labels. Give the same short practice task before timing.
4. Start the timer when a reviewer opens a passage and stop after all in-scope fields are recorded. Log elapsed seconds for each reviewer, document, and mode, plus corrections and unresolved items. Compare paired per-document times; report median time and the difference between modes. Keep training time separate.

Record observations in `backend/eval/independent_dutch/review_time_log.csv`. **No reviewer ran this protocol**, so reviewer time saved is unmeasured; provider runtime is not a substitute for review time.

## Limits

This is a small, purposive, single-labeler challenge set, not a representative clinical evaluation. Each field has only 1–3 labeled examples, including few negative or absent cases. It does not measure inter-rater agreement, clinical validity, workflow quality, or performance across hospitals and report templates. Results should guide error analysis only and must not support clinical use claims.
