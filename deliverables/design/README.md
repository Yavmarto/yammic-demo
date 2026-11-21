# Design deliverables (W6)

Visual direction v2 for the connected demo. The full spec is `../D7b_visual_direction.md`.

## Contents

| Path | What it is |
|---|---|
| `critique/v2_*.png` | Screenshots of the committed v2 build at 1440x900 and 1280x800, used in the critique |
| `tokens/design_tokens.json` | Source of truth for colour, state, type, space, radius, motion, breakpoints |
| `tokens/zeta_theme_extension.dart` | Copy-ready Flutter `ThemeExtension` + `buildYammicTheme(ThemeData)`; analyzed clean on Flutter 3.47.5 |
| `prototype/index.html` | Static, self-contained visual reference for all eight screens plus a states sheet |
| `prototype/shots/*.png` | 1440x900 screenshots of each prototype frame |

## Open the prototype

```
open deliverables/design/prototype/index.html
```

It is a single local file: no fonts, scripts, or data are fetched from the network. Frames are 1440x900 and scale to the browser width. Scroll the page to compare screens. The index at the top jumps to each screen.

The prototype is a **static reference**, not production code. The Flutter app is the source of truth for data and interaction. Use the prototype for composition, token values, and before/after discussion.

## Key rules

- Light mode only in the demo. Tokens keep a semantic layer for later dark mode.
- Accent is Zeta `mainPrimary` `#0073E6`; text links use `#005BB8`.
- Green is reserved for human-verified clinical data. Teal is system integrity (FHIR connection, audit chain). Amber is an AI proposal. Red is rejected/conflict.
- Every state has icon + text + shape, never colour alone.
- IBM Plex Sans weights 300 / 400 / 500 only.
- No shadows on panels; 1 px borders and surface tints do the work.
- No chart package: the charts are `CustomPainter` in the app and inline SVG in the mock.

## Regenerate the screenshots

The screenshots were captured with Playwright + Chromium from the static file:

```
node -e "const {chromium}=require('playwright'); ..."
```

The capture script is not committed because it depends on a local Playwright cache. The reference frames are committed as PNGs. If the HTML changes, re-capture each `.frame` element at 1440x900 and replace `prototype/shots/*.png`.

## Contrast checks

All text and state pairs in the spec pass WCAG 2.2 AA. The measured ratios are in `D7b_visual_direction.md` §3.1 and in `tokens/design_tokens.json` under `color.contrast`.

## Ownership

Designer (W6). The Engineer (W7) owns the Flutter implementation. Do not edit `app/` from this folder; the spec is the handoff.
