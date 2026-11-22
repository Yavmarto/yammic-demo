# v4 design references

Static visual reference for the five v4 features. The implementation contract is
[`deliverables/D7c_v4_screens.md`](../../D7c_v4_screens.md); this folder only shows the intended look.

## Open

- Full reference: open `index.html` in a browser (no server needed).
- One frame: `index.html?only=1` … `?only=6`.

## Shots

| Shot | Frame |
|---|---|
| `shots/01_screening.png` | Screening queue + criteria checklist + sign-off gate |
| `shots/02_site_comparison.png` | Dashboard site switcher + comparison panel |
| `shots/03_queries_sdv.png` | Queries inbox, thread, field context, monitor SDV |
| `shots/04_participant_timeline.png` | Participant timeline + source evidence rail |
| `shots/05_protocol_form.png` | Protocol → form builder + approval rail |
| `shots/06_states.png` | Empty, loading, error, offline and blocked states |

## Regenerate

```bash
./capture.sh
```

The script uses the Playwright headless shell already on this machine. Override it with
`CHROME=/path/to/headless_shell ./capture.sh` if needed. Frames are 1440 × 900 at scale 1.

## Visual rules

Same v3 tokens as `app/lib/theme/tokens.dart`: canvas `#F3F6FA`, surface `#FFFFFF`, accent
`#0073E6`, AI amber `#FEF2E2/#B26A00`, verified green `#ECFFF7/#4EA26B`, rejected/not met red
`#FFF0F1/#D70015`, integrity teal `#E7F7F7/#1A8080`, unknown/planned grey. One accent, 1 px
borders, no shadows on panels, 8/12/16/999 radii, IBM Plex Sans 300/400/500 only.

This is not production code. The Flutter widgets and tokens are named in D7c.
