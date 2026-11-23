# Dutch abstention and evidence challenge

This is a separate, synthetic, hand-labelled challenge set. The labels and source evidence were written before either provider was run. It does not alter the original generator or arrivals cases. The 10 short notes contain 21 labelled field decisions, including seven expected abstentions. Cases cover absent values, conflicting pathology text with a superseding addendum, hedged/noisy imaging, and ordinary positive values.

Run from `backend/`:

```sh
uv run python -m eval.challenge.run --provider rules
uv run python -m eval.challenge.run --provider ollama --timeout 240
```

Results are isolated under `eval/challenge/results/{provider}/`. `latest.json` contains per-document predictions, failures, per-field decision accuracy and proposal-value F1, correct abstentions with their gold-abstention denominator, exact evidence-string agreement, invalid source-span count, model ID, and run limits. Exact-span agreement is measured only for labelled positive decisions. An invalid source span is any proposed evidence span that fails the existing source locator. Failed documents remain visible in the result and are not scored as correct.

The challenge uses the installed local Ollama model only; no network model service is called. Ollama generation uses temperature 0, seed 42, and at most 240 seconds per document. A timeout is retained as a timeout in the result.

The task requested local `dev` base `22e65a7`, but that revision is absent from this checkout. This branch was created from the available local `dev` HEAD `bcc0f74`.

A second labelled set can be run with `--dataset`, for example `uv run python -m eval.challenge.run --provider rules --dataset eval/abstention_v2/dataset.json`. Non-default sets write to `results/<provider>-<folder>/`, so the frozen challenge results are not overwritten. The CEL-1857 abstention set (`eval/abstention_v2/`) was used for tuning and is a regression fixture, not a held-out measure.
