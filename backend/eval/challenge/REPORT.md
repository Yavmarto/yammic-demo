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
