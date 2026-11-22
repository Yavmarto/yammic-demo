# Integrated provider comparison — `8e4132f`

## Run record

- **Commit:** `8e4132f7249ac71c52530070d6a0ac32f2427b28` (`Record the write-back API contract and benchmark provenance`)
- **Dataset:** `dutch-abstention-evidence-challenge-v1`, 10 frozen synthetic documents and 21 labelled field decisions; SHA-256 `0d37f04ccf221a30b66702f1fd2a3bd3d3b91cff326cf15c32ccd7ab026f24bf`.
- **Model:** local Ollama `qwen2.5:7b-instruct`, digest `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`; free local model, no remote service.
- **Ollama settings:** temperature 0, seed 42, 8192 context, 240-second timeout per document.
- Both archived JSON files include the full commit, prompt SHA-256, model digest (where applicable), dataset SHA-256, run time, document status and failures. `result.md` files give per-field summaries.

## Results

| Measure | Rules | Ollama |
|---|---:|---:|
| Decision accuracy | 19/21 (0.9048) | 17/21 (0.8095) |
| Correct abstentions / gold abstentions | 6/7 | 6/7 |
| Exact evidence spans / labelled positive decisions | 12/14 | 1/14 |
| Invalid source spans | 0 | 0 |
| Completed / missing outputs | 10/10 / 0 | 10/10 / 0 |
| Timeouts | 0 | 0 |
| Elapsed time | 4 ms | 120,751 ms |
| Prompt version | `rules_v1@83a90473b9fb` | `extract_v4@1ef2060c673d` |
| Prompt SHA-256 | `83a90473b9fb02176a900f98df96dcab56b5d64aaabe6ac996e526c1843d2f96` | `1ef2060c673d52423df5237ec46a5c4edc03f78e5e0c5e035d946b2ed9b2b0b8` |

The integrated comparison matches the recorded CEL-1844 provider counts: rules 19/21 decisions, 6/7 abstentions and 12/14 exact spans; Ollama 17/21, 6/7 and 1/14. It confirms those results on the requested integrated commit. The rules prompt SHA-256 here is `83a904…`; it differs from the rules prompt recorded on integrated dev before this run, so prompt identity is part of the comparison. The Ollama prompt SHA-256 is `1ef206…`.

## Interpretation and limits

The recorded comparison continues to support rules as the deterministic baseline for this synthetic extraction challenge, with Ollama as a comparison point for development. This is a narrow engineering recommendation from the earlier comparison; this rerun confirms the same metric ordering. It is not evidence of clinical performance or reviewer-time savings. No prompt or provider tuning was done on the frozen cases. No real records were used. Reviewer time was not measured. Zero invalid spans only means returned evidence strings were locatable in source text; it does not establish clinical sufficiency.

The previous comparison and its results remain in the existing provider `latest.json`/`latest.md` files and the original report. This rerun is kept separately in this directory.
