# D7b - Visual direction v2 (connected demo)

**Owner:** Designer (W6) · **For:** Engineer (W7), CEO, QA · **Date:** 2026-11-21
**Status:** Implementation spec, committed on `dev`
**Replaces:** the visual layer of `D7_demo_screens.md` (its interaction rules for UI-005 and the audit remain valid)
**Scope:** login, dashboard, participant workspace, UI-005 review, audit trail, integrations, AI quality, export.
**Plan:** [CEL-1727 plan v3](</CEL/issues/CEL-1727#document-plan>) · **Code freeze:** Sun 2026-11-22 20:00 CET.

Read this with:
- `04_REQUIREMENTS_SPEC.md` (FR-001, FR-002, FR-022, FR-035, FR-038, FR-040, FR-042, FR-045, FR-050..059)
- `05_UX_UI_SPEC.md` §1 (AI output must not look like confirmed data), §3 (UI-001/002/005/007), §4 (journeys)
- `06_ARCHITECTURE_STANDARDS_AI.md` §3 (evidence spans, model and prompt registry, precision/recall)
- `07_REGULATORY_SECURITY.md` §5 (validation, traceability)
- The existing scaffold: `app/lib/models/models.dart`, `app/lib/data/repository.dart`, `app/lib/theme/tokens.dart`, `app/lib/ui/widgets.dart`

Everything here is implementable with **Zeta 1.4.5 + custom Flutter widgets**. No new packages, no chart library, no network calls from the UI.

---

## 0. One-page summary for the Engineer

Build the app as a **calm clinical instrument**: a dark-ink wordmark, a quiet cool-grey canvas, white data panels with 1 px borders, one blue accent, and a strict three-cue grammar for AI vs verified data. Dense tables, monospaced numbers, no decorative shadows, no page-load animation, no dark mode.

Ship these eight surfaces:
1. **Login** (local demo accounts, role cards, no SSO).
2. **Dashboard** (metric strip, recruitment chart, site table, AI queue).
3. **Participant workspace** (timeline, eCRF, quality, treatment Gantt, right rail).
4. **UI-005 review** (three panes, evidence highlight, fixed action bar).
5. **Audit trail** (dense table, chain-verified badge, event detail panel).
6. **Integrations** (FHIR connection, sync history, sync steps).
7. **AI quality** (per-field precision/recall, model + prompt registry).
8. **Export** (ODM / FHIR format cards, validation, step stepper, result).

Hard rules:
- Only IBM Plex Sans weights **300, 400, 500** exist in Zeta. Do not use 600 or 700.
- Accent is Zeta `mainPrimary` **#0073E6**. Text links use **#005BB8**. Never mix a second blue.
- Green is reserved for **human-verified clinical data**. Use teal for connection integrity. Use amber for AI proposals. Use red for rejected/conflicting values.
- Every state has icon + text + shape. Colour is never the only signal.
- Use `Panel`, not Material `Card`. Use custom rows, not `ListTile`, for data.
- No dark mode in this demo. Tokens are structured so it can be added later.
- Keep the synthetic-data banner on every screen.

---

## 1. Honest critique of the v2 UI

Evidence: `deliverables/design/critique/v2_*.png` (captured from the committed v2 build at 1440x900 and 1280x800).

### 1.1 Verdict

The v2 app does not look ugly because it uses Zeta. It looks ugly because **it barely uses Zeta and has no visual system**: Material defaults, one column of boxes, default blue/olive progress bars, no data visualisation, no density, no hierarchy, and no product shell. The review screen is the only surface with a real idea; it still reads as four different button styles on one card.

### 1.2 Findings, with evidence

| # | Finding | Evidence | Why it matters |
|---|---|---|---|
| 1 | **No product shell.** 112 px icon rail, no wordmark, no study context, no role, no connection state. | `v2_dashboard_1440.png` | The app reads as a prototype, not a platform. The demo story needs a connected product, so the chrome must say "platform". |
| 2 | **No hierarchy.** Page title, section headings, and body differ by size only; every section is the same full-width stack. | dashboard, participant | The eye has nowhere to land. The most important data (recruitment, AI queue) is visually equal to milestones. |
| 3 | **Wasted canvas.** One 340 px card floats in a 1,250 px content area; the participant page is a single 1,250 px column of lists. | dashboard, participant | Users scan 3x farther than needed. Dense clinical work needs a grid, not a column. |
| 4 | **Material defaults leak through.** Default `Card` radius/elevation, `LinearProgressIndicator` blue + muddy olive, `ListTile` rows, default `Chip` outlines. | dashboard, participants, audit | The result looks like a Flutter sample. Zeta's tokens are not applied consistently. |
| 5 | **Button grammar is inconsistent.** `Accept` filled blue, `Correct` filled olive, `Reject` blue text, `Defer` blue outline. | `v2_review_1440.png` | Four weights for one decision row. The olive reads as disabled or dirty. Users hesitate at the safety-critical moment. |
| 6 | **No data visualisation.** Recruitment is a default progress bar. No trend, no site comparison, no precision/recall, no sync history, no treatment bar. | all screens | The v3 story is "connected data". Without charts and dense tables, the connection is invisible. |
| 7 | **The audit trail is not a table.** Full-width rows with no columns, no header, no detail panel, no chain badge, no hash. | `v2_audit_1440.png` | An auditor cannot compare time, actor, action, field, and change. The regulatory value is lost. |
| 8 | **1280 is not tuned.** Target value wraps mid-ID, action buttons wrap onto two rows, source measure gets too wide. | `v2_review_1280.png` | The demo laptop view looks broken, which is exactly what the Board sees. |
| 9 | **Empty and loading are generic.** Full-screen spinners, dead space, "No visits" rows. | code + screens | The demo loses its story when the backend is down or a queue is empty. The offline story needs designed states. |
| 10 | **No motion language.** Route changes are instant, bars jump, no feedback on sync or verification. | live run | Motion is not decoration here: sync, extraction, and verification are state changes that need subtle confirmation. |

### 1.3 Design health score (Nielsen, v2)

Honest scoring for the v2 build. The target for v3 is 32+/40.

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of system status | 1 | No connection, sync, extraction, or verification status outside the review pane. |
| 2 | Match system / real world | 3 | Clinical labels are correct. The visual language is not clinical. |
| 3 | User control and freedom | 2 | Dedicated panes exist; no undo, no back pattern beyond the rail. |
| 4 | Consistency and standards | 1 | Mixed Material and Zeta components; four button styles; olive as a system colour. |
| 5 | Error prevention | 3 | Accept is blocked without evidence. Good. Reject reason is required. |
| 6 | Recognition rather than recall | 2 | Filters and shortcuts exist but are not surfaced. |
| 7 | Flexibility and efficiency | 2 | Keyboard shortcuts in review; no command palette, no batch affordance in the UI. |
| 8 | Aesthetic and minimalist design | 1 | Empty space without purpose; no hierarchy; no data-viz. |
| 9 | Error recovery | 2 | Snackbars and validation exist; no offline/retry story, no chain verification. |
| 10 | Help and documentation | 1 | A shortcut tooltip only. |
| **Total** | | **18/40** | Poor. The review flow is the only strength. |

### 1.4 What v2 got right (keep it)

1. **Three-pane review.** Source, proposed values, target is the right model for evidence-linked review. Keep the structure, rebuild the surface.
2. **Safety rule.** Unverified AI output is amber, dashed, and labelled. Accept is disabled without a span. This is the core safety idea; formalise it into a token system.
3. **Synthetic banner.** The warning is honest and persistent. Keep it, but make it 28 px and calm instead of a heavy amber bar.
4. **Keyboard shortcuts.** A/C/X/D/J/K plus a help tooltip. Keep and display them as `Kbd` hints.

### 1.5 The single biggest opportunity

Make the **connection visible**: a live sync, an AI queue with confidence, a chain-verified audit badge, precision/recall per field, and a valid export. Those five artefacts turn a list-based mock into a platform story. The visual direction must give each one a compact, high-trust component.

---

## 2. Art direction: "Calm instrument"

### 2.1 The scene sentence

> A research nurse at a 27-inch monitor in a bright hospital office, mid-morning, moving between a pathology report and a 46-item review queue for 45 minutes, while a monitor watches the same data read-only on a second screen.

That scene forces **light mode**, **dense but quiet surfaces**, **one accent**, and **numbers that align**. It rules out dark dashboards, neon AI chrome, glassmorphism, and marketing-style hero metrics.

### 2.2 The idea

The interface should feel like a **well-kept lab instrument**: precise, labelled, calm, and honest about uncertainty. Not a consumer health app, not a futuristic AI console. The data is the colour; the chrome is almost silent.

Three references, and what to take from each:
- **Linear / Height**: a slim left rail, a crisp top context bar, dense lists, one accent, no card soup.
- **Stripe Dashboard**: tabular numbers, quiet borders, a strict neutral scale, charts that are readable without legends everywhere.
- **Clinical instruments (lab analysers, anaesthesia monitors)**: every value has a unit, a timestamp, a source, and a state. Alarm colours are rare and meaningful.

Anti-references:
- White cards on a white page with drop shadows.
- Rainbow dashboards.
- Purple-blue AI gradients as decoration.
- Glassmorphism.
- Big-number hero cards with a sparkline and a gradient.
- Dark mode "because tools look cool dark".

### 2.3 Principles

1. **One accent, one alarm at a time.** Blue is action. Amber is AI. Green is human-verified. Red is rejected/conflict. Teal is system integrity. If two colours compete on a screen, one is wrong.
2. **Density with air.** Clinical users need more data per screen, not less. Use dense tables and a 12-column grid, then separate sections with 32 px, not 8.
3. **Show the source.** Every AI value, every KPI, every sync has a source, a time, and a state. No orphan numbers.
4. **Borders, not shadows.** One-pixel rules and surface tints create structure. Shadows are reserved for overlays only.
5. **Motion confirms, never performs.** 120-240 ms, ease-out, no bounce, no orchestrated page load.
6. **The demo must survive failure.** Offline, empty, loading, and error states are designed, not fallback text.

### 2.4 Dark mode decision

**No dark mode in the v3 demo.** The scene is daylight desk work; the QA budget is better spent on states, charts, and the new screens. The token file keeps a semantic layer so a dark theme can be added later without touching components. If someone asks on stage, say: "Light-first for clinical review; the token layer supports dark mode in production."

If dark mode is added later:
- Surfaces: `#151519` (canvas), `#1D1E23` (panel), `#24262C` (raised).
- Text: `#F3F6FA` primary, `#BBC1CB` secondary.
- Accent: desaturate ~10%, use `#599FE5`.
- No shadows; depth from surface steps.
- Bump body line-height by 0.05 and add 0.01em tracking.

---

## 3. Foundations: tokens on top of Zeta

**Implementation rule:** Zeta is the base. Do not replace Zeta's `ThemeData`; layer a semantic extension and a small set of custom widgets on top. Use Zeta components for inputs, buttons, dialogs, snackbars, tooltips, chips, progress, and navigation. Use the custom widgets in §8 for the shell, panels, tables, charts, and state pills.

Token files:
- `deliverables/design/tokens/design_tokens.json` (source of truth)
- `deliverables/design/tokens/zeta_theme_extension.dart` (copy-ready Flutter)
- The live implementation already started in `app/lib/theme/tokens.dart`; keep the names `K.*` and the `Panel` / `PageHeader` / `Pill` / `Bar` / `Kbd` / `FadeIn` widgets, and extend them with the values below.

### 3.1 Colour roles

Every value below is checked against its actual background. `Zeta token` is the semantic token this role extends.

| Role | Token | Value | Zeta token | Use |
|---|---|---|---|---|
| Canvas | `canvas` | `#F3F6FA` | `surfaceCool` tinted | app background behind panels |
| Surface | `surface` | `#FFFFFF` | `surfaceDefault` | panels, tables, forms |
| Sunken | `surfaceSunken` | `#EEF2F7` | `surfaceHover` | table header, sidebar, inset wells |
| Hover | `surfaceHover` | `#F3F6FA` | `surfaceHover` | row hover |
| Selected | `surfaceSelected` | `#F1F8FF` | `surfaceSelected` | selected nav item, selected row |
| Border subtle | `line` | `#E4E9F0` | `borderSubtle` | dividers, panel borders |
| Border default | `lineStrong` | `#CED2DB` | `borderDefault` | table rules, inactive controls |
| Input border | `inputLine` | `#8A94A6` | none | inputs (3.06:1 on white) |
| Ink | `ink` | `#1D1E23` | `mainDefault` | primary text, headings |
| Ink 2 | `ink2` | `#545963` | `mainSubtle` | secondary text, metadata |
| Ink 3 | `ink3` | `#667085` | none | labels, captions (4.97:1 on white) |
| Accent | `accent` | `#0073E6` | `mainPrimary` | primary action, selection, focus base |
| Accent ink | `accentInk` | `#005BB8` | `statePrimarySelected` | text links, pressed state (6.59:1) |
| Accent soft | `accentSoft` | `#F1F8FF` | `surfacePrimarySubtle` | selected nav, info tint |
| Focus ring | `focus` | `#005BB8` | none | 3 px outer ring, 2 px white gap |

Verification and system states. **These are the only colours allowed for data state.**

| State | Surface | Border | Ink | Icon | Label |
|---|---|---|---|---|---|
| **AI proposal (unverified)** | `#FEF2E2` | `#B26A00` (dashed 2 px) | `#6E4A00` | `Icons.auto_awesome` | `AI · Unverified` |
| **Verified accepted** | `#ECFFF7` | `#4EA26B` (solid 2 px) | `#0C5734` | `Icons.check_circle_outline` | `Verified · Accepted` |
| **Verified corrected** | `#ECFFF7` | `#4EA26B` (solid 2 px) | `#0C5734` | `Icons.edit_note` | `Verified · Corrected` |
| **Rejected** | `#FFF0F1` | `#D70015` (solid 2 px) | `#8F000E` | `Icons.block` | `Rejected` |
| **Deferred** | `#F3F6FA` | `#8A94A6` (solid 1 px) | `#3F4B58` | `Icons.schedule` | `Deferred` |
| **Abstained** | `#F3F6FA` | `#8A94A6` (dashed 2 px) | `#3F4B58` | `Icons.help_outline` | `AI abstained` |
| **Conflict** | `#FFF0F1` | `#D70015` (solid 2 px) | `#8F000E` | `Icons.warning_amber_rounded` | `Conflict` |
| **Connected (system)** | `#E7F7F7` | `#1A8080` (1 px) | `#0B4F4F` | `Icons.link` + dot | `Connected` |
| **Syncing (system)** | `#FEF2E2` | `#B26A00` (1 px) | `#6E4A00` | `Icons.sync` | `Syncing` |
| **Offline (system)** | `#F3F6FA` | `#8A94A6` (1 px) | `#3F4B58` | `Icons.cloud_off` | `Offline snapshot` |

Contrast evidence (WCAG 2.2 AA):
- AI ink 6.77:1 on AI surface; AI border 4.24:1 on white, 3.84:1 on AI surface.
- Verified ink 8.32:1; verified border 3.13:1.
- Rejected ink 8.73:1; rejected border 5.33:1.
- Deferred ink 8.21:1.
- Accent 4.57:1 on white; accent ink 6.59:1; focus 6.59:1.
- Ink3 4.97:1 on white, 4.59:1 on canvas.
- Never put grey text on an AI/verified surface. Use that state's ink.

Do not use:
- Zeta `mainSecondary` (olive) for buttons, progress, or selection. It was the ugliest single element in v2.
- Green for connection status, workflow status, or AI success.
- Red for routine "remove" actions. Reject is quiet (text button) until the user commits in the reason dialog.
- The Zeta AI card gradient (`isAi: true`) except for a small 16 px "AI running" sparkle badge. It is too loud for a 46-card queue.

### 3.2 Chart palette

Use at most three colours in one chart. Always label axes and units.

| Token | Value | Use |
|---|---|---|
| `chart1` | `#0073E6` | actual/primary series |
| `chart2` | `#1A8080` | secondary series, integrity/connection |
| `chart3` | `#8D7400` | tertiary series, target line |
| `chart4` | `#D30589` | fourth series only when needed |
| `chartPositive` | `#00864F` | verified/positive delta |
| `chartGrid` | `#E4E9F0` | gridlines, 1 px |
| `chartMuted` | `#A7B0BE` | forecast, previous period |

Rules:
- Area fills are the series colour at 10-12% opacity. Never a gradient.
- Lines are 2 px, no smoothing beyond a monotone curve, no drop shadows.
- Bars are 8 px max, 4 px gap, square on the baseline, 2 px radius on the data end only.
- Numeric labels use tabular figures, `ink2`, 11-12 px.
- Legends are direct labels at the end of the line when possible; otherwise a 12 px legend row above the chart.
- Tooltips are `ZetaTooltip` or a custom `ChartTooltip` at 240 px, 1 px border, no shadow.
- Do not use pie/donut charts. Use a stacked bar or a table.

### 3.3 Typography

Zeta ships IBM Plex Sans at weights 300, 400, 500 only. Use **500 as the maximum**. Hierarchy comes from size, colour, and space, not synthetic bold.

| Role | Size / line | Weight | Tracking | Use |
|---|---|---|---|---|
| `display` | 32 / 40 | 500 | -0.4 | page title, one per screen |
| `h1` | 24 / 32 | 500 | -0.2 | section title, dialog title |
| `h2` | 20 / 28 | 500 | 0 | card/panel title |
| `h3` | 16 / 24 | 500 | 0 | field group, table section |
| `body` | 14 / 21 | 400 | 0 | default UI text |
| `bodyLarge` | 15 / 26 | 400 | 0 | source document text, max 68ch |
| `small` | 12.5 / 18 | 400 | 0 | metadata, helper |
| `label` | 11 / 16 | 500 | 0.08em, uppercase | table headers, metric labels |
| `numeric` | 14 / 20 | 500 | 0 | table numbers, tabular |
| `metric` | 28 / 34 | 500 | -0.3 | metric strip values, tabular |
| `mono` | 12 / 18 | 400 | 0 | hashes, IDs, XML, before/after |

Rules:
- **Tabular figures everywhere**: `fontFeatures: [FontFeature.tabularFigures()]` on numeric, metric, mono, and all table cells.
- Document text measure caps at **68ch**. Do not let source text run the full pane width.
- Line length for prose 65-75ch. Tables may run denser.
- No all-caps sentences. All-caps only for `label`.
- No display font. No second family. System monospace (`Menlo`, `SF Mono`) for hashes and code is fine.
- Text scale: 100% and 200% must work. At 200%, panes stack internally; no clipped labels.
- Placeholders use `ink3` at minimum; never a lighter grey.

### 3.4 Spacing and grid

4 pt base: `4, 8, 12, 16, 24, 32, 48, 64`.
- Page padding: 24 at ≥1440, 20 at 1280.
- Panel padding: 20 (default), 24 (form, empty state).
- Grid: 12 columns, 16 px gutter, max content width 1440. The sidebar is outside the grid.
- Section gap: 32. Panel gap: 16. Related row gap: 8. Inline icon gap: 6.
- Rhythm: KPI strip is tight (12), then a 32 gap to the chart row, then 16 between panels. Avoid equal gaps everywhere.
- Table row: 44 px default, 40 px dense, 56 px for two-line rows.
- Touch/click targets: 40 px minimum for primary controls, 32 px for icon buttons, 24 px absolute minimum.

Breakpoints (Zeta `DeviceType`):
| Width | Sidebar | Page | Review panes | Dashboard |
|---|---|---|---|---|
| ≥1440 | 232 expanded (72 on UI-005) | 24 | 520 / 340 / 420 | 12 col, chart 8 + queue 4 |
| 1280-1439 | 72 collapsed | 20 | 440 / 320 / 360 | 12 col, chart 8 + queue 4 |
| 1024-1279 | 72 collapsed | 20 | 2 panes + tab for target | 8 col, chart + queue stacked |
| <1024 | 64 rail | 16 | single pane, tabs | single column |

At 200% text scale, the review screen switches to the 2-pane + tab layout early.

### 3.5 Radii and elevation

| Element | Radius | Elevation |
|---|---|---|
| Input, button, chip container | 8 | none |
| Panel, card, table container | 12 | none (1 px `line`) |
| Dialog, popover, command palette | 16 | `0 8px 24px rgba(16,24,40,0.10), 0 2px 6px rgba(16,24,40,0.06)` |
| Pill / status chip | 999 | none |
| Evidence highlight | 3 | none |
| Avatar | 999 | none |

No shadows on panels, tables, nav, or the top bar. Sticky headers use a 1 px bottom border, not a shadow. This is the main visual difference from v2's default Material cards.

### 3.6 Icons

- Use **Zeta icons** (`zeta_icons` package, round style) for navigation and status. Use Material Icons only when Zeta has no equivalent.
- Sizes: 16 inline metadata, 20 default, 24 nav, 32 empty-state.
- One style per screen. Do not mix filled and outline in the same list.
- Icons never replace text for a state. Pair with a label.
- Status icon map: AI `auto_awesome`, verified `check_circle_outline` / `edit_note`, rejected `block`, deferred `schedule`, abstained `help_outline`, conflict `warning_amber_rounded`, connected `link`, syncing `sync`, offline `cloud_off`, verified chain `verified_user`.
- Avoid icon-only buttons except: close, overflow, copy, prev/next. All get tooltips and 40 px hit areas.

### 3.7 Motion

| Token | Duration | Curve | Use |
|---|---|---|---|
| `fast` | 120 ms | `Curves.easeOutCubic` | hover, press, colour change |
| `base` | 180 ms | `Curves.easeOutCubic` | selection, chip change, fade-in |
| `slow` | 240 ms | `Curves.easeOutCubic` | panel reveal, side sheet |
| `scroll` | 200 ms | `Curves.easeOut` | evidence scroll, row focus |
| `exit` | 90 ms | `Curves.easeInCubic` | dismiss, collapse |

Rules:
- No page-load choreography. The app opens into the task.
- Progress bars animate once from 0 to value over 420 ms, then never re-animate on rebuild.
- Sync: status dot pulses once (600 ms) on state change, not looping. A live sync row may show an indeterminate 2 px bar.
- Verification: the affected card crossfades from amber to green in 180 ms and the target value fades in 120 ms. No slide, no confetti.
- Evidence scroll: `Scrollable.ensureVisible` 200 ms. If `MediaQuery.disableAnimations`, duration zero.
- Skeletons: opacity 0.4-0.7, 1.2 s, only when reduce-motion is off.
- Never animate width/height/margins. Use opacity, color, and transforms only.

### 3.8 Density and content rules

- Show units on every clinical value (`7.2 mmol/L`, `KPS 90`, `60 Gy`).
- Show the source and timestamp for imported values in metadata, not in a badge on every row.
- Dates: `23 Nov 2026`, times: `14:04` (24h) with `CET` in detail views. Use the fixed `demoToday = 2026-11-23`, never `DateTime.now()`.
- IDs: pseudonyms `GBM-NL-001`; resources `DOC-001-PATH`, `ext-1042`, `obs-8842`, hashes `0x8f3a...c21d`.
- Copy: plain English (Dutch later). Short labels. No marketing tone inside the app.
- Empty states tell the next action. Error states say what failed, what to do, and whether data is read-only.

---

## 4. Shell, navigation, and global chrome

### 4.1 Shell layout

```
┌ Synthetic data banner 28 ─────────────────────────────────────────────────────┐
├──────────────┬────────────────────────────────────────────────────────────────┤
│ Sidebar 232  │ Top context bar 56: breadcrumb · study · sync · role · user     │
│              ├────────────────────────────────────────────────────────────────┤
│ Yamicc       │ Screen content (page padding 24, max 1440)                      │
│ Study        │                                                                │
│  Dashboard   │                                                                │
│  Participants│                                                                │
│  AI review 5 │                                                                │
│  Audit trail │                                                                │
│ Platform     │                                                                │
│  Integrations│                                                                │
│  AI quality  │                                                                │
│  Export      │                                                                │
│              │                                                                │
│ ● FHIR 42ms  │                                                                │
│ SYN-JD nurse │                                                                │
└──────────────┴────────────────────────────────────────────────────────────────┘
```

- Sidebar: 232 expanded, 72 collapsed. UI-005 always uses the 72 px focus rail so the three panes fit at 1440. Background `surfaceSunken`, 1 px right border `line`. No shadow.
- Wordmark: "Yamicc" in `h2` 20/500, with a 24 px square mark (ink background, white "Y" or a simple 3-node graph). Do not use a hospital cross.
- Nav sections with 11 px uppercase `label` headings: `STUDY` and `PLATFORM`.
- Nav item: 40 px high, 8 px radius, 12 px icon, 8 px gap, 14 px label. Selected: `surfaceSelected` background, 1 px `borderPrimary`? No, use background + accent icon + 500 weight. No side stripe.
- Badges: AI review shows the pending count in a neutral `ZetaTag`; if >0, amber dot + number. Audit has no badge.
- Footer: connection pill and role menu. Connection pill: 8 px dot + `FHIR · 42 ms` (teal if connected, amber syncing, grey offline). Role menu: `ZetaAvatar` initials + name + role, opens a `ZetaDropdown` or `ZetaBottomSheet` with "Switch demo role".
- Top context bar 56: breadcrumb (12.5 px), study chip, "Data as of 23 Nov 2026", a `ConnectionPill`, and a 32 px avatar menu. On scroll, the bar stays fixed; content scrolls under it with a 1 px border.
- Command palette (recommended): `Ctrl/Cmd+K`, 560 px wide, 16 radius, search nav + participants + actions. It is a strong "slick" signal and helps the demo move fast. If time is short, ship the keyboard shortcut to the AI queue only.
- Synthetic banner: 28 px, `#FEF2E2` background, 1 px `#F0D3A8` bottom border, `Icons.science_outlined` 14, text 12.5/500 `#6E4A00`: "Synthetic data · Prototype, not for clinical use". Right side: `DEMO` tag. Not dismissible. At 200% text, height grows, never clips.
- Offline banner: 32 px under the top bar, `surfaceSunken`, `cloud_off`, "Offline snapshot. Read-only until the local backend reconnects." with a "Retry" text button. All write buttons disabled with a tooltip.

### 4.2 Navigation and routes

| Route | Screen | Sidebar | Role visibility |
|---|---|---|---|
| `/login` | Login | none | all |
| `/dashboard` | Dashboard | Dashboard | nurse, monitor, PI |
| `/participants` | Participant list | Participants | nurse, monitor, PI |
| `/participants/:id` | Participant workspace | Participants | nurse, monitor, PI |
| `/review/:id?` | UI-005 review | AI review | nurse, PI (monitor read-only) |
| `/audit` | Audit trail | Audit trail | all |
| `/integrations` | Integrations | Integrations | nurse (read), PI |
| `/ai-quality` | AI quality | AI quality | PI, monitor (read) |
| `/export` | Export | Export | PI, monitor (read) |

Route transitions: 120 ms fade only, no slide, no shared-axis. Preserve scroll position on back.

### 4.3 Role behaviour

| Action | Research nurse | Monitor | PI |
|---|---|---|---|
| View dashboard, participants, audit | yes | yes | yes |
| Accept/correct/reject/defer AI values | yes | no (read-only banner) | yes |
| Sync FHIR | yes | no | yes |
| Run evaluation | no | no | yes |
| Generate export | no | no | yes |
| Verify chain | yes | yes | yes |

Disabled actions stay visible with a tooltip: "Monitor role is read-only in this demo." Do not hide the function entirely; the demo needs to show the role difference.

---

## 5. Screen specs

Each spec names the exact widgets and token values. Wireframes are structure, not pixel truth; dimensions are at 1440 unless stated.

### 5.1 Login

**Goal:** enter the local demo in one click and understand the three roles.

**Layout:** split 44/56 at ≥1200; single column below.

```
┌───────────────────────────────┬──────────────────────────────────────────────┐
│ BRAND PANEL #0E1B2C           │  Sign in                                     │
│                               │  Local demo · synthetic data                 │
│ Yamicc                        │                                              │
│ Clinical research,            │  [ Research nurse ] [ Monitor ] [ PI ]       │
│ connected.                    │                                              │
│                               │  Email        [ nurse@demo.yamicc         ]  │
│ One connected record from     │  Password     [ ••••••••              ] [e]  │
│ hospital to regulator-ready   │  [ ] Remember me on this machine            │
│ evidence.                     │                                              │
│                               │  [ Sign in                              ]    │
│ ● Local backend healthy       │  Use demo account · Forgot password          │
│ FHIR R4 · Postgres 16         │                                              │
│                               │  SSO is disabled in the local demo.          │
└───────────────────────────────┴──────────────────────────────────────────────┘
```

- Brand panel: `#0E1B2C`, white text, a subtle 1 px grid or contour pattern at 4% white. No gradient. A 32 px wordmark, 32/40 `display` headline, 14/22 body at `#9FB3C8` (8.05:1).
- Form card: white, 480 px wide, 40 px padding, 16 radius, 1 px `line`. Centered vertically.
- Role cards: 3 equal cards, 44 px high, 8 radius, 1 px `line`; selected has `surfaceSelected` + 2 px `accent` border + check icon. Each shows role name and a 12 px line ("eCRF + review", "Read-only SDV", "Study + export"). Selecting a role prefills the email. This is demo-only; production would derive the role from identity.
- Inputs: `ZetaTextInput`/`ZetaPasswordInput` 44 px, 8 radius, `inputLine` border, 2 px `accent` on focus, label above (not placeholder-only). Password has a reveal icon.
- Primary button: full width, 44 px, `accent`, white 14/500, 8 radius. Loading: 16 px spinner + "Signing in..." and disabled.
- Secondary: "Use demo account" text button in `accentInk`.
- Footer: "SSO is disabled in the local demo" 12 px `ink3`; `Local backend healthy` with a teal dot.
- Error: `ZetaInPageBanner(status: negative)` above the form, "We could not sign you in. Check your email and password." Focus the email field. Do not clear the email.
- Empty: not applicable. Loading: button state only. Offline: banner "Local backend is down. Start it with `make demo`, then retry." with Retry.

**Widgets:** `LoginScreen`, `BrandPanel`, `LoginCard`, `RoleCard`, `ZetaTextInput`, `ZetaPasswordInput`, `ZetaButton.primary`, `ZetaCheckbox`, `ZetaInPageBanner`, `ConnectionPill`.

**Acceptance:** one click from "Use demo account" to dashboard in under 800 ms; three roles switch the sidebar visibility; keyboard-only path works; no real credentials.

### 5.2 Dashboard (UI-001)

**Goal:** in 5 seconds, the PI sees recruitment, completeness, open work, and the AI queue. In 15 seconds, the coordinator knows what to do next.

**Layout:** page header, metric strip, 12-col grid.

```
┌ Page header: Research dashboard        [Study: GBM-NL-2026-01 v] [23 Nov] ┐
│ ReDiReCT-GB · 3 sites · last sync 2 min ago                              │
├──────────────────────────────────────────────────────────────────────────┤
│ METRIC STRIP   Enrolled 8/24  Active 6  eCRF 71%  Queries 9  AI queue 46  │
├─────────────────────────────────────────────┬────────────────────────────┤
│ Recruitment (8 col)                         │ AI review queue (4 col)    │
│  bars + cumulative line + target             │ 46 pending · low first      │
│                                             │ [Review queue →]           │
├─────────────────────────────────────────────┼────────────────────────────┤
│ Site performance (8 col)                    │ Alerts + next milestone    │
│ table: site, enrolled, queries, completeness│ (one 4-col panel)          │
├─────────────────────────────────────────────┴────────────────────────────┤
│ Tasks due (7 col)                         │ Recent activity (5 col)      │
└──────────────────────────────────────────────────────────────────────────┘
```

**Metric strip:** one continuous white panel with 5 segments separated by 1 px `line`, 92 px high. No 5 floating cards. Each segment: `label` 11/500 uppercase `ink3`, value `metric` 28/500 tabular `ink`, delta `small` with a 12 px arrow (`+3 this week` in `chartPositive`, `-2` in `mainNegative`), optional 48x18 sparkline. The Enrolled segment has a 2 px progress bar at the bottom (value/target). The AI queue segment has an amber dot and a chevron; it links to review.
- Values from the API: enrolled, active, completeness (verified only), open queries, AI pending. Never add AI-pending to completeness.
- Loading: 5 skeleton blocks inside the strip, same widths.

**Recruitment chart:**
- 12-week composed chart, 120-140 px tall in the 1440x900 frame (the static mock uses 112 px; allow the page to scroll at 200% text). At larger screens, 180-220 px is fine.
- Bars: weekly enrollments, `chart1` at 22% opacity, 8 px, 4 px gap.
- Line: cumulative enrolled, `chart1` 2 px, monotone.
- Dashed target line: `chart3` 1.5 px, dashed 4/4, direct label "Target 24".
- Axis: 4 horizontal gridlines `chartGrid`, y labels 11 px `ink3` tabular, x labels every 2 weeks.
- Annotation: a 1 px vertical line + 10 px dot for "First patient in" at week 2, label `small` `ink2`.
- Hover: `ChartTooltip` with week, new, cumulative, target. 12 px padding, 1 px `line`, 8 radius, no shadow.
- Empty: "No recruitment data yet. Sync the FHIR connection to load participants." with a "Sync now" link.
- Loading: skeleton axis + 8 bars.
- Error: inline panel error "Recruitment data unavailable. Showing the offline snapshot." Keep the last snapshot with an "Offline" pill.

**Site table:**
- Columns: Site (flex), Enrolled (88, right), Queries (72, right), Completeness (120: value + 48 px bar), Last sync (96), Status (96).
- 40 px dense rows, header `label` on `surfaceSunken`, sticky. Divider 1 px `line`. Hover `surfaceHover`. Selected `surfaceSelected`.
- Site name two lines max: "FUMC Zuidhaven" + "fictional · Site 01" 11 px `ink3`.
- Status: neutral pill (`Active`, `Paused`) with an icon. Do not use verified green.
- Sort: open queries desc by default; clickable header for enrolled/completeness.
- Footer: "3 sites · 8 enrolled · 9 open queries" 12 px `ink3`.
- Empty: "No sites for this study." + "Show all studies".

**AI review queue card:**
- Header: "AI review" + `46` tag; subline "Lowest confidence first".
- 3 rows, 44 px: field label, participant ID, confidence as a 3-segment meter (low <0.7, medium 0.7-0.9, high >0.9) + number, and a tiny state icon. Low confidence first; abstained has a dashed help icon. Put the queue CTA in the header ("46 pending · Review →"); do not add a footer row. A fourth row clips the card at 1440x900.
- A 4 px stacked bar at the top: pending amber, verified green, rejected red, deferred grey.
- Footer: "46 pending · 2 abstained" + `Review queue →` (`accentInk`).
- Empty: "Queue clear. All values reviewed." + check icon + "Open audit trail".
- Loading: 4 skeleton rows.

**Alerts and milestones:**
- Alerts: 2 rows, 44 px, plus one "Next milestone" row in the same panel. Severity icon 16 (`info_outline` blue, `warning_amber_rounded` amber, `error_outline` red), 1 line message, 1 line study/time. "View all" text button. Do not put milestones in a separate 78 px card; it clips at 1440x900.
- Severity uses solid amber for warnings, not the dashed AI treatment. The icon and the word "Warning" carry the meaning.
- Milestones: a 3-row mini timeline with a 8 px dot, 1 px connector, name, date. Group upcoming/done. No big list.
- Empty: "No alerts" / "No milestones due" with a check; do not render an empty panel.

**Tasks due:**
- 3 rows, 44 px: title, assignee avatar 20, due date (mono), overdue red dot + "Overdue" text. Row click opens the participant or a task detail side sheet.
- Empty: "No tasks due this week." + "View all tasks".

**Recent activity:**
- 3-4 audit rows, 40 px: time mono, actor, action, field, source dot. "View audit trail" link.
- This makes the platform feel alive and connects the dashboard to the audit story.

**Widgets:** `PageHeader`, `MetricStrip`, `Metric`, `Panel`, `RecruitmentChart` (CustomPainter), `SiteTable`, `DataTableHeader`, `QueueCard`, `AlertRow`, `MilestoneTrail`, `TaskRow`, `ActivityRow`, `Skeleton`, `EmptyPanel`, `ErrorPanel`.

**Acceptance:** all KPIs from the API; AI queue count separate from completeness; chart readable at 1280 with no label collision; table has a header and aligned numerics; no default Material Card/ListTile; empty/loading/error for each panel.

### 5.3 Participant workspace (UI-002)

**Goal:** one pseudonymised participant, with verified clinical data, visit progress, eCRF status, quality issues, treatment history, and the AI queue in one screen.

**Layout:** page header, main 8 col + right rail 4 col.

```
┌ Participants / GBM-NL-001        [Open eCRF] [Review AI (3)]  ⋯          ┐
│ GBM-NL-001  [Active]  GBM-NL-2026-01 · Site 01 · 57 y · F               │
├───────────────────────────────────────────────┬─────────────────────────┤
│ Clinical summary (verified only)              │ AI review queue (3)     │
│ 2 lines + "Source: FHIR · synced 2 min ago"   │ 3 rows + Review →       │
│                                               ├─────────────────────────┤
│ Visit timeline                                │ Demographics            │
│  Screening  ● 22 May  ✓ completed   eCRF 100% │  Age, sex, site, study  │
│  Baseline   ● 05 Jun  ✓ completed   eCRF 100% │  Pseudonym, consent     │
│  ...                                          ├─────────────────────────┤
│                                               │ Source & sync           │
│ eCRF status                                   │  FHIR R4 · 2 min ago    │
│  table: form, progress, status, pending       │  Provenance 4 records   │
│                                               ├─────────────────────────┤
│ Quality issues (2)                            │ Recent audit (3)        │
│ Treatment history (Gantt)                     │  ...                    │
└───────────────────────────────────────────────┴─────────────────────────┘
```

**Header:** breadcrumb `Participants / GBM-NL-001`. `display` ID + neutral status pill. Meta line 12.5 px `ink2`: study · site · age · sex · consent `Active`. Right: `Open eCRF` outline, `Review AI (3)` primary with the pending count, overflow menu (`Copy pseudonym`, `Open audit filtered`, `Flag for SDV`).
- Withdrawn: a `ZetaInPageBanner(status: warning)` "Participant withdrawn. Data is read-only." Disable eCRF and review actions; keep audit visible.
- Monitor role: replace `Review AI` with `Open review (read-only)`, and show a "Read-only SDV" pill.

**Clinical summary panel:** verified-only text, max 68ch, 15/26. A 12 px source line: `FHIR R4 · Observation/Condition · synced 14:02`. A small "Verified data only" lock icon with a tooltip. If there are pending AI values, show a separate amber inline note "3 values await review" with a link, never inline in the summary.
- Empty: "No verified clinical summary yet." + "Review AI values".

**Visit timeline:** vertical rail with grouped phases (`Screening`, `Treatment`, `Follow-up`). Each row 56 px:
- Left: date column 72 px, mono 12 px.
- Center: 20 px node (filled accent for completed, outline for scheduled, red outline for missed) on a 1 px connector.
- Main: visit name 14/500, note 12.5 `ink3`.
- Right: eCRF mini progress ring 24 px + `100%` or `2 pending`; a status pill.
- Click: inline expansion (not a modal) with visit details and a "Open eCRF" link. Expansion 180 ms.
- Missed: red node + `Missed` + `event_busy`. Scheduled: outline node + `Scheduled`.
- Empty: "No visits scheduled." + `event_available`.
- Loading: 5 skeleton rows.

**eCRF status panel:** compact table, header `Form`, `Progress`, `Status`, `Pending`, `Updated`. 40 px rows. Progress = 64 px bar + `62%` tabular. Status pills: neutral for not started/complete, accent-soft for in progress, amber dashed for awaiting review. Pending count links to review.
- Empty: "No eCRF forms for this visit." 

**Quality issues panel:** 2-3 rows. Severity icon (low info blue, medium amber triangle, high red error), field name 12 px, message 14 px, "Open" link. Show at most 3 with "View all". Empty: "No open quality issues." + check.

**Treatment history:** a Gantt-style regimen chart, 120 px tall. A shared month axis; each regimen is a 12 px bar with a label and dose; ongoing bars have an arrow end. TMZ cycles as 6 segments. Hover shows start/end/dose. This is the data-viz moment that makes the workspace feel clinical, not a list.
- Empty: "No treatment recorded." 
- Loading: axis + 2 skeleton bars.

**Right rail:**
- AI queue card: 3 rows (field, confidence, state icon), "Review all 3 →". Empty: "Nothing awaiting review." + check.
- Demographics: key-value rows (Age, Sex at birth, Study, Site, Consent, Pseudonym). 12 px labels `ink3`, 14 px values.
- Source & sync: FHIR endpoint, last sync, resources, provenance count, "Open integration" link.
- Recent audit: 3 rows (time, actor, action) + "View all".
- Each card is a `Panel`; no nested cards. Use dividers inside.

**Widgets:** `PageHeader`, `Panel`, `StatusPill`, `VisitTimeline`, `VisitNode`, `EcrfTable`, `QualityRow`, `RegimenGantt`, `QueueCard`, `KeyValueList`, `ActivityRow`, `EmptyPanel`.

**Acceptance:** pending AI never appears in the summary/treatment; timeline groups and expands; Gantt is readable at 1280; withdrawn/monitor read-only states work; all sections have empty/loading.

### 5.4 UI-005 AI extraction review

**Goal:** review 46 AI-proposed values against their source, with evidence, confidence, mapping, and a safe accept/correct/reject/defer path. This is the centrepiece; it must feel fast and calm.

**Layout:** full-height workspace, no page scroll.

```
┌ AI review / GBM-NL-001 / Visit V8        [Participant v] [Batch] [?]      ┐
│ Review 46 AI values      ▓▓▓▓▓░░░░░ 1 of 46 reviewed · 45 pending        │
│ [All] [Needs review] [Low confidence] [Abstained]                         │
├──────────────────────────────┬──────────────────┬────────────────────────┤
│ SOURCE                       │ PROPOSED VALUES  │ TARGET eCRF            │
│ Pathology report · DOC-001   │ 46 fields        │ Histology              │
│ p.2 · 05 Jun 2026            │ ┌──────────────┐ │ Glioblastoma, IDH-wt   │
│                              │ │ Histology    │ │ [AI · Unverified]      │
│ text with the evidence span  │ │ 0.98  ●●●    │ │                        │
│ highlighted in amber, with   │ └──────────────┘ │ Evidence 1 of 2        │
│ a superscript marker and the │ ...              │ Provenance ▾           │
│ evidence navigator below.    │                  │ ─────────────────────  │
│                              │                  │ [Accept] [Correct]     │
│                              │                  │ [Reject] [Defer]       │
└──────────────────────────────┴──────────────────┴────────────────────────┘
```

**Top bar (72 px; the sidebar collapses to the 72 px focus rail on this screen):**
- Breadcrumb 12 px `ink3`: `AI review / GBM-NL-001 / Visit V8`.
- Title `h1` "Review 46 AI values" + a 160 px progress bar (`ZetaProgressBar`, 4 px) + "1 of 46 reviewed · 45 pending" 12 px.
- Right: participant `ZetaDropdown` (all participants + current), `Batch` toggle (`ZetaSwitch` or toggle button), `?` shortcuts `IconButton`, overflow `More`.
- Filter row 40 px: `ZetaSegmentedControl` All / Needs review / Low confidence / Abstained, plus a search field 240 px (field or participant). Active filter persists per participant.
- No global app bar; this screen owns its header to maximize height.

**Pane widths at 1440:** source 520, proposed 340, target 420, gaps 16, padding 20. At 1280: 440 / 320 / 360. At <1280: source + proposed, target becomes a 40% side sheet or a tab.
- Panes are `Panel` with 0 padding, header 44 px, body scrolls independently with `Scrollbar`.
- Pane header: `label` uppercase `ink3` + a count/status on the right. 1 px bottom border.

**Source pane:**
- Header: document type + ID (`PATHOLOGY REPORT · DOC-001-PATH`) and a metadata line (`Received 05 Jun 2026 · p.2 · 3 evidence spans`). A document switcher dropdown if the participant has multiple docs.
- Body: 15/26, max 68ch, 24 px padding. Use `SelectableText.rich`.
- Evidence span: `surfaceWarning` background `#FEF2E2`? For text highlight use `#FFE1A8` (soft amber) with a 2 px `#B26A00` bottom border and a 4 px radius. Active span: `#FFD08A` + 2 px `#8A5A00` underline + a small superscript marker `1` in an amber pill. Inactive spans: `#FFF1D6` with no underline.
- Do not tint the whole paragraph. Only the exact span.
- Evidence navigator at the bottom of the source pane, 44 px: `Evidence 1 of 2 · p.2 ¶3` + prev/next chevrons + a "Reveal" text button. The navigator is also the accessible text alternative: `Semantics(label: 'Evidence for histology: ...')`.
- If the span is invalid: a `ZetaInPageBanner(status: warning)` "No evidence span. Accept is disabled. Correct, reject, or defer." and no highlight.
- Clicking a span selects the matching proposed card and scrolls the list. Selecting a card scrolls the source to the span.

**Proposed pane:**
- Top summary 40 px: 4 segments of a 4 px bar (accepted green, corrected green, rejected red, deferred grey) + counts `1 verified · 45 pending` in 11 px.
- List grouped by field group (`Diagnosis`, `Molecular`, `Treatment`, `Outcomes`). Group header 32 px `label` + count. Sort within a group: abstained, low confidence, pending, done. This is the key change from v2: the reviewer sees the uncertain items first.
- Card: 12 px radius, 1 px border, 12 px padding, 8 px gap. Selected: 2 px `accent` border + `surfaceSelected` tint; do not use a left stripe.
  - Row 1: field label 12.5/500 `ink` + participant ID 11 px `ink3`.
  - Row 2: value 20/500 tabular, unit 12 px `ink2`.
  - Row 3: status pill + confidence 3-segment meter + `0.98` tabular + evidence icon (`Icons.link` if span valid, `link_off` if not).
  - Low confidence (<0.70): amber "Low confidence" text + `warning_amber` 14, never a red border.
  - Abstained: `AI abstained` dashed pill, value shows "Not stated", evidence icon off.
  - Done cards: 70% opacity, status pill, a small check; still clickable to inspect.
- Batch mode: a 20 px checkbox appears at the left of each card; a sticky footer 56 px with "3 selected" + `Accept selected` + `Clear`. Confirmation is a `ZetaDialog` listing fields; one audit event per field; invalid fields are excluded and listed.

**Target pane:**
- Header: `TARGET eCRF · Histology` + a required marker + a "Read-only" lock if the role/record is locked.
- Value block: 24/32 tabular value + unit. For a pending AI value, show a **ghost** value in `ink3` with a dashed 1 px box and the amber pill; the actual eCRF value is "Not entered".
- Status pill + a 1-line validation message if any.
- Evidence line: `Evidence 1 of 2 · p.2 ¶3` with a back-link to the source. Clicking it focuses/scrolls the source.
- Provenance block, collapsed (`ZetaAccordion`): extraction id, model, prompt version, proposed at, reviewer, audit event id, `View audit trail`.
- **Action bar fixed at the bottom** of the pane, 64 px, 1 px top border, `surface`. Buttons 40 px, all same height, 8 radius:
  - `Accept` primary (accent), `A` hint.
  - `Correct` secondary (outline), `C` hint.
  - `Defer` tertiary (text, `ink2`), `D`.
  - `Reject` quiet destructive (text, `mainNegative` text but no red fill), `X`.
  - A 12 px line "Enter/A accept · C correct · X reject · D defer" or `Kbd` chips. Do not repeat this line on every card; put it in the header and a `?` dialog.
- Accepted/corrected: the value block turns green, shows "Verified by SYN-JD · 14:02", and the action bar becomes `Next field` primary + `Undo` text (5 s). The card in the middle updates to a green check.
- Correct mode: inline editor replaces the value; 44 px `TextField`, unit suffix, validation text below, `Save correction` primary + `Cancel` outline. Keep the original AI value in a 12 px muted line "AI proposed: 7.1".
- Conflict: show a 2-column compare (`Current eCRF` vs `AI proposal`), both values, a `Conflict` pill, and `Keep existing` / `Replace with AI` actions. Both are audit-logged. Never silently overwrite.
- Abstained: value block "No evidence in source"; Accept disabled with a tooltip; `Correct` is primary; `Reject`/`Defer` available.
- Empty: "All 46 values reviewed." + a 4-segment summary + `Open audit trail` + `Back to participant`. Calm, no confetti.
- Loading: 3-pane skeleton, no spinner. After 500 ms, a 3 px `ZetaProgressBar` under the header: "Loading synthetic study data...".
- Error: per-pane inline `ErrorPanel`; if the AI service is down, a banner "AI service unavailable. Rules provider is active." with `Retry extraction`. If the backend is down, the offline banner + read-only.
- Invalid span: block Accept, keep Correct/Reject/Defer, show the reason.

**Keyboard:**
- `A` accept, `C` correct, `X` reject, `D` defer, `J`/`Down` next, `K`/`Up` previous, `B` batch, `H` toggle inactive highlights, `?` shortcuts, `Esc` cancel dialog/correction, `Ctrl/Cmd+Z` undo last action.
- Single letters are disabled while a text field has focus.
- Every action is available by mouse. Focus ring 3 px `#005BB8` with a 2 px white offset. `SemanticsService.announce` after every decision.
- `Tab` order: header filters → source → proposed → target → actions. Each pane is a `FocusTraversalGroup`.

**Accessibility:**
- Status is icon + text + shape (dashed/solid). Grayscale test must distinguish all states.
- Confidence is text (`0.98 · high`), not colour only. Screen reader: "Confidence 0.98 of 1, high".
- Evidence highlight has a text alternative in the navigator.
- 200% text: cards grow; no clipped values; target pane scrolls; action bar wraps to 2 rows if needed but remains visible.

**Widgets:** `ReviewWorkspace`, `ReviewHeader`, `ReviewPane`, `SourcePane`, `EvidenceHighlight`, `EvidenceNavigator`, `ProposedList`, `ProposedCard`, `ConfidenceMeter`, `TargetPane`, `ActionBar`, `ConflictCompare`, `ProvenanceAccordion`, `BatchFooter`, `Kbd`, `StatusPill`, `Skeleton`.

**Acceptance:** three panes fit at 1440 and 1280 with the widths above; Accept disabled without evidence; every action writes one audit event with before/after/model/prompt; low-confidence first sorting; conflict never overwrites; batch produces one event per field; full keyboard pass; grayscale pass; 200% pass.

### 5.5 Audit trail (UI-012 evidence view)

**Goal:** prove that every AI proposal and human decision is attributable, ordered, and tamper-evident.

**Layout:** header, chain badge, filters, table + detail side panel.

```
┌ Audit trail                         [Verify chain] [Export log]            ┐
│ Append-only, hash-chained. 1,284 events.                                   │
├────────────────────────────────────────────────────────────────────────────┤
│ [shield] Chain verified · 1,284 events · checked 12s ago  0x8f3a...c21d    │
├────────────────────────────────────────────────────────────────────────────┤
│ [All | AI | Human] [Action v] [Participant v] [Search]  [23 Nov v]        │
│ Time    Actor   Source  Action  Participant  Field        Change      Hash │
│ 14:04   JD      [AI]    correct GBM-NL-001   Histology    WT → IDH-wt  8f3a│
│ ...                                                                        │
├──────────────────────────────────────────────────────────┬─────────────────┤
│ Table                                                    │ Event detail    │
│                                                          │ chain, hashes   │
└──────────────────────────────────────────────────────────┴─────────────────┘
```

**Chain badge:**
- Verified: teal `#E7F7F7` panel, 1 px `#1A8080`, `verified_user` 20 teal, "Chain verified" `h3`, second line "1,284 events · last checked 12 s ago · SHA-256", short hash mono, `Verify again` text button. Height 64.
- Verifying: neutral panel, 16 px spinner, "Verifying 1,284 events...", button disabled. 600 ms demo.
- Broken: red `#FFF0F1` panel, `gpp_bad`/`shield` icon red, "Chain broken at event #0042", "Expected prev-hash does not match. Data may have been altered.", `Inspect` primary/outline. A debug-only "Simulate tamper" action lives in the `⋯` menu, not on stage by default.
- Unavailable: grey panel, `cloud_off`, "Verification unavailable. The audit service is unreachable." + Retry.
- The badge is deliberately teal, not green: green means human-verified clinical data; teal means system integrity. This distinction is part of the visual language.

**Table:**
- Columns (fixed layout, ellipsis + tooltip): Time 72, Actor 100, Source 64, Action 62, Participant 88, Field 104, Change flex, Hash 96, chevron 32. At 1440 the table is about 788 px and the detail 340; at 1280 the table is about 720 and the detail 300.
- 40 px rows, sticky header `label` on `surfaceSunken`, 1 px dividers. Right-aligned? No, all left except hash. Numeric/time mono tabular.
- Actor cell: 20 px avatar initials + `SYN-JD`; source badge: AI amber pill with sparkle, Human green pill with person (this is the one place green is used for a human actor; the label "Human" and the icon carry it; do not use green for the row background).
- Action chip: neutral, icon + label (`extract`, `accept`, `correct`, `reject`, `defer`, `undo`, `sync`).
- Change cell: mono `7.1 → 7.2`, with `n/a` for null. Truncate with a tooltip at 1280.
- Hash: first 8 chars mono `8f3a...`, `ZetaTooltip` with full hash. This makes the chain visible without a wall of hex.
- Row click selects and opens the detail panel (inline 340 at 1440, 300 at 1280, not a modal). Keyboard: `Up/Down` moves, `Enter` opens, `Esc` closes. Do not wrap the Change column; truncate long values and show the full text in the detail panel.
- Hover `surfaceHover`, selected `surfaceSelected`, no zebra stripes.

**Filters:**
- `ZetaSegmentedControl` All / AI / Human.
- Action `ZetaDropdown` (All, Extract, Accept, Correct, Reject, Defer, Undo, Sync).
- Participant `ZetaDropdown` (All + IDs).
- Search `ZetaSearchBar` 240, debounce 150, matches actor, participant, field, event id. `Esc` clears.
- Date chip `23 Nov 2026` (demo fixed) + `Last 7 days`.
- Result count 12 px `ink3`; "Clear filters" link when any filter is active.
- Empty filter: "No events match these filters." + Clear.

**Event detail panel:**
- Header `Event #01284` + event id mono + a copy icon.
- A vertical chain strip at the top: `prev 7d21...` → `this 8f3a...` → `next 2c90...`, 3 rows with 1 px connectors, hashes mono. This is the tangible chain.
- Key-value rows: Time, Actor + role, Source (AI/Human), Action, Participant, Field, Before, After, Model, Prompt, Extraction, Evidence link, Hash, Prev hash, Signature (demo key).
- `Copy event JSON` outline button; `Open in review` for extract events still in the queue; `Filter by participant` link.
- Footer 12 px: "Append-only. No edit or delete. Hash chain verified." 
- For an AI event, show the model/prompt and the evidence span; for a human event, show the reviewer and the before/after.

**States:** loading skeleton badge + 8 rows; empty "No audit events yet. Accept, correct, reject, or defer a value to create the first entry." + Open review; error "Could not verify chain. Retry."; offline read-only banner; filtered empty.

**Widgets:** `AuditScreen`, `ChainBadge`, `AuditTable`, `AuditRow`, `SourceBadge`, `ActionChip`, `EventDetailPanel`, `HashChip`, `ChainStrip`, `FilterBar`, `Skeleton`.

**Acceptance:** every UI-005 action appears with actor/source/before/after/model/prompt/time; filters and search work; verify chain transitions; detail panel shows prev/this/next hashes; no edit/delete; 1280 has no horizontal scroll (truncate + tooltip).

### 5.6 Integrations (new, UI-007)

**Goal:** show that the platform is connected to a local hospital FHIR server, that sync is healthy, and that new data can arrive live.

**Layout:** header, connection card, two-column stats/history.

```
┌ Integrations                         [Add connection] [Sync now]          ┐
│ Hospital connections and data sync. Local demo, no internet.              │
├──────────────────────────────────────────────────────────────────────────┤
│ [HAPI] Erasmus MC · HAPI FHIR R4            ● Connected  42 ms  R4       │
│ http://localhost:8090/fhir                                  [copy]       │
│ Last sync 2 min ago · next in 13 min · 8 participants · 46 documents      │
│ [Sync now] [Test connection]                              ⋯             │
├───────────────────────────────────────┬──────────────────────────────────┤
│ Sync history (8 col)                  │ Mapping coverage (4 col)         │
│ table: started, trigger, resources,   │ mCODE 92% · LOINC 88%            │
│ new, updated, errors, status          │ SNOMED 84% · "Review mappings"   │
├───────────────────────────────────────┴──────────────────────────────────┤
│ Sync detail (when a row is selected): steps, counts, errors, logs         │
└──────────────────────────────────────────────────────────────────────────┘
```

**Connection card:**
- 88-104 px tall, white panel, 12 radius, 1 px `line`. The static mock uses 104 to fit the metadata line.
- Monogram 40 px: `#0E1B2C` square, white "H" or "FHIR" 12/500; no external logo assets.
- Name `h2` + "HAPI FHIR R4" 12 px; endpoint mono 12 px with a copy icon (tooltip "Copy endpoint").
- Status: `Connected` pill (teal dot + link icon), latency `42 ms`, FHIR version `R4`, "TLS off (local)" in `ink3` (honest for the demo).
- Meta line: last sync, next sync, participants, documents. Separate with 12 px bullets.
- Actions: `Sync now` primary, `Test connection` outline, overflow `Edit mapping`, `View logs`, `Disable`.
- Syncing: status pill amber `Syncing 12/46`, `Sync now` becomes disabled with a 16 px spinner, a 2 px indeterminate bar under the card, and the history gets a live row at the top. On completion, pulse the dot once and toast "Sync complete. 3 new documents, 2 updated."
- Error: status red `Authentication failed (401)` + "Check the FHIR client credentials." + `Retry` + `View logs`. The card border becomes red; do not hide the endpoint.
- Offline: grey `Backend unreachable`, actions disabled, offline banner.

**Stats row:** 4 inline stats separated by 1 px lines: Resources 1,284; Participants 8; Documents 46; Errors 0. Use the metric typography at 20/500, not a hero.

**Sync history table:**
- Columns: Started 120, Trigger 88, Duration 72, Resources 88, New 64, Updated 72, Errors 64, Status 96.
- 6-8 rows, 40 px, header on sunken, sticky. Status pills: `Completed` neutral/teal, `Running` amber with a 12 px spinner, `Failed` red.
- Row click opens a detail drawer/side panel 400: a vertical `SyncSteps` timeline (Authenticate, CapabilityStatement, Patient match, Pull resources, Pseudonymise, Extract, Store) with timestamps, counts, and any error text. A monospace log excerpt at the bottom, 8 lines, with a copy button. No full log wall.
- Empty: "No syncs yet. Run the first sync to pull synthetic hospital data." + Sync now.
- Loading: 5 skeleton rows.

**Mapping coverage card:**
- 3 rows: `mCODE 92%` (bar), `LOINC 88%`, `SNOMED 84%`, each with a small 48 px bar and a count. A note "3 unmapped fields" in amber + `Review mappings →` (placeholder for UI-008; if not built, a `ZetaTooltip` "Mapping workspace is out of scope for this demo").
- Empty: "No mappings loaded." 

**Add connection:** primary button opens a `ZetaDialog`/side sheet with fields (Name, FHIR base URL, Auth: none / basic / token, Test connection). For the demo, it can be disabled with a tooltip "One local connection is configured for this demo." Do not fake a second connection.

**Widgets:** `IntegrationsScreen`, `ConnectionCard`, `StatusDot`, `SyncHistoryTable`, `SyncSteps`, `MappingCoverage`, `EndpointField`, `MetricRow`, `ZetaInPageBanner`, `EmptyPanel`, `Skeleton`.

**Acceptance:** sync runs and updates counts/history; live step timeline; connection state changes; errors show actionable text; no network beyond localhost; empty/loading/error/offline states.

### 5.7 AI quality (new, UI-009-style)

**Goal:** show precision, recall, abstention per field, and a model + prompt registry. This is the evidence that the AI is governed, not magic.

**Layout:** header, metric strip, per-field table + detail, registry.

```
┌ AI quality                 [Provider v] [Rules · prompt p-2026-11-07]    ┐
│ Gold-set evaluation on the synthetic cohort. No patient data.            │
├──────────────────────────────────────────────────────────────────────────┤
│ Precision 0.94   Recall 0.89   F1 0.91   Abstention 7%   Reviewed 46/46 │
├───────────────────────────────────────┬──────────────────────────────────┤
│ Per-field precision / recall (8 col)  │ Field detail (4 col)             │
│ table + paired bars, n, delta          │ TP/FP/FN, examples, error types  │
├───────────────────────────────────────┴──────────────────────────────────┤
│ Model & prompt registry                                                    │
│ model, type, prompt, status, last run, precision, recall, abstain          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Header:** title `AI quality`, subtitle "Gold-set evaluation on the synthetic cohort (n=46 fields, 46 documents)." Right: provider `ZetaDropdown` (`Rules (deterministic)`, `Ollama · local`, `Claude · disabled`), model/prompt chip `demo-extractor-v0.3 · p-2026-11-07`, `Run evaluation` outline, last run "12 min ago".
- Claude option: disabled row with a lock icon and "Paid API, Gate 3 approval required". This makes the gate visible without enabling it.
- Running: button spinner + "Running 46 fields..." + a 2 px progress bar; results update when done.

**Metric strip:** 5 compact segments: Precision, Recall, F1, Abstention, Reviewed. Put the median review time in the subtitle, not a sixth segment, so the strip does not crowd at 1280. Same component as the dashboard. Delta vs previous run: `+0.02` teal, `-0.03` red, with an arrow. Do not use green for a positive delta: green is verified; use teal for positive metric deltas to avoid semantic collision. Good: `chart2` for positive, `mainNegative` for negative.

**Per-field table:**
- Columns: Field (flex), n (48), Precision (80 + bar), Recall (80 + bar), Abstain (64), Δ vs last (64), status (icon).
- Paired bars: 64 px track, 6 px height, precision `chart1`, recall `chart2`, 2 px gap, numeric label right. No rainbow.
- Sort by lowest recall first. A small `Regression` tag (amber outline) on fields that dropped >2 pp.
- Rows: Histology, MGMT promoter methylation, IDH status, KPS, Resection extent, Diagnosis date, Age, Sex, Planned cycles, Radiotherapy dose.
- Row click selects; the right detail panel updates.

**Field detail panel:**
- Header: field name + n + "Gold labels: 46".
- A small confusion matrix: 2x2 grid of TP/FP/FN/TN, 64 px cells, `chartPositive` for TP/TN at 10% fill, `mainNegative` for FP/FN at 10%. Numbers tabular. This is compact and more useful than a chart.
- Error breakdown: missed (FN), wrong value (FP), hallucinated (FP), abstained correctly, abstained incorrectly. Horizontal bars or a small table.
- 2 example cards: source span + gold value + predicted value + outcome pill. This proves the evaluation is real.
- Empty: "Select a field to see error examples." 

**Model & prompt registry:**
- Table/cards: Model (`demo-extractor-v0.3`), Type (`Rules`), Prompt (`p-2026-11-07`), Status (`Active`), Last run, Precision, Recall, Abstain, Actions (`View prompt`).
- Rows: rules active; `ollama:qwen2.5-7b` active (local, free); `claude` disabled (paid, Gate 3); an older rules `v0.2` archived with its metrics for regression context.
- `View prompt` opens a read-only `ZetaDialog` with the prompt name, version, hash, and a 12-line monospace excerpt. No editing in the demo.
- A 12 px note: "Every extraction run logs model + prompt version. Evaluation is a regression gate, not a one-off report." 
- Empty: "No evaluation yet. Run the first evaluation on the gold set." + Run evaluation.

**Widgets:** `AiQualityScreen`, `MetricStrip`, `PerFieldTable`, `PRBar`, `ConfusionMatrix`, `ErrorBreakdown`, `ExampleCard`, `RegistryTable`, `PromptDialog`, `DeltaBadge`, `EmptyPanel`, `Skeleton`.

**Acceptance:** provider switch updates the label and (if rules vs ollama data differs) the metrics; disabled Claude is visible with the Gate 3 reason; per-field bars and numbers align; field detail updates; registry shows model + prompt version for every run; empty/loading/error.

### 5.8 Export (new, UI-004-adjacent)

**Goal:** generate a valid CDISC ODM XML or FHIR QuestionnaireResponse + Provenance bundle, see the validation result, and push it back to the local FHIR server.

**Layout:** header, 7/5 form + preview, history.

```
┌ Export                         [Export history] [New export]             ┐
│ Regulator-ready package with provenance. Synthetic data only.            │
├──────────────────────────────────────────┬───────────────────────────────┤
│ Format                                   │ Summary                       │
│ [CDISC ODM XML 1.3.2]  [FHIR R4 QR + Prov]│ 42 participants               │
│ Scope: study, sites, participants, dates │ 46 documents                  │
│ Options: audit trail, sign, push         │ 1,284 observations            │
│ Validation: ✓ schema valid · 2 warnings  │ File tree preview             │
│ [Generate export]                        │ manifest.json, data.xml, ...  │
│ Steps: Collect → Transform → Validate →  │ SHA-256 after generation      │
│ Package                                  │                               │
├──────────────────────────────────────────┴───────────────────────────────┤
│ Export history table: date, format, scope, status, size, checksum, action │
└──────────────────────────────────────────────────────────────────────────┘
```

**Header:** "Export", subtitle "Regulator-ready package with source provenance. Synthetic data only." Right: `Export history` text button + `New export` primary (or the form is the default and `New export` resets it).

**Format cards (2):**
- `CDISC ODM XML 1.3.2`: "Clinical data interchange. Includes study metadata, eCRF data, and audit references." Badge `Schema validated`.
- `FHIR R4 Bundle`: "QuestionnaireResponse + Provenance + Observation resources for write-back." Badge `Profile validated`.
- Cards 72-96 px tall, radio selection, 2 px accent border + check when selected. A small mono format code (`odm` / `fhir`). These are true choices, so cards are appropriate.
- At 1280 they stay side by side; at <1100 they stack.

**Scope form:**
- Study: fixed `GBM-NL-2026-01` (locked).
- Sites: multi-select `ZetaDropdown` (3 sites, all selected).
- Participants: `All 8` / `Filtered` (status, site) / `Selected` (chips). For the demo, `All 8`.
- Date range: `From 01 Jun 2026` / `To 23 Nov 2026` (`ZetaDateInput`).
- Include: 
  - `Include audit trail` checked, disabled for ODM? Actually ODM can include audit; keep checked and explain.
  - `Include provenance` checked, locked for FHIR.
  - `Sign with demo key` unchecked (a demo key; no real signature).
  - `Pseudonymised only` checked, locked, with a lock icon.
- All labels visible; no placeholder-only fields.

**Validation summary:**
- Before generate: "Ready. 42 participants, 1,284 observations, 2 warnings." with a green check? Green is verified; use teal check for validation. Warnings use amber, errors red.
- Warnings: "2 values are missing a diagnosis date. They will be exported as null with a provenance flag." + `Open review` link. Do not block on warnings; block on errors.
- If errors: "3 required fields are missing." red + list + `Fix in review` primary.

**Generate:**
- Primary `Generate export` 44 px. On press, the button becomes disabled + 16 px spinner, and a 4-step `StepTrail` appears below: Collect (0.2s), Transform (0.4s), Validate (0.3s), Package (0.2s). Each step: 20 px circle (pending grey, active accent spinner, done check), label, right-aligned count/elapsed. 180 ms step transitions.
- Result card: file name `yamicc_export_GBM-NL-2026-01_2026-11-21T1042Z.zip`, size `1.8 MB`, SHA-256 mono truncated with copy, `Download` primary, `Push to FHIR` outline, `Open history` text. A `Validated` teal pill. The download is a local file; no network.
- Push to FHIR: separate 600 ms step, then "Bundle accepted (201). Provenance written." toast; on 422, "FHIR server rejected the bundle" + `View response` dialog with the OperationOutcome. Push is idempotent; disable after success and show `Pushed 14:04`.

**Preview (right 5 col):**
- Summary counts: participants, documents, observations, audit events.
- File tree: `manifest.json`, `data.xml` or `bundle.json`, `provenance/`, `README.txt`, `checksums.sha256`; each with a size in mono.
- A 12-line XML/JSON snippet in a `surfaceSunken` well, 12 px mono, `ink2`, horizontal scroll, no syntax rainbow. Label `Preview (first 12 lines)`.
- Last export card: date, format, status, size, checksum.

**Export history:**
- Table: Date, Format, Scope, Status, Size, SHA-256, Actions. 5 rows. Status `Validated` teal, `Failed` red, `Pushed` teal outline. `Download` icon button, `View` row click.
- Empty: "No exports yet. Build the first package." 
- Loading: skeleton rows.

**States:** generating (stepper + disabled), success (result card), validation error (red list), push error (dialog), offline (read-only), empty history. No modal for the result; inline is faster and demo-stable.

**Widgets:** `ExportScreen`, `FormatCard`, `ScopeForm`, `OptionRow`, `ValidationSummary`, `StepTrail`, `ExportResult`, `FileTree`, `CodePreview`, `ExportHistoryTable`, `ZetaCheckbox`, `ZetaDateInput`, `ZetaButton`.

**Acceptance:** both formats generate locally; ODM validates against the schema; FHIR bundle validates and pushes; warnings do not block; errors block with a clear path; checksum copied; history updates; no real data, no external network.

---

## 6. Cross-screen components

### 6.1 StatusPill

Anatomy: 24 px high, 8 px horizontal padding, 999 radius, 1 px or 2 px border, 13 px icon, 12/500 label, optional 6 px leading dot. Dashed variants use a `CustomPainter` (`DashedBorderPainter`), not a package.
- AI: dashed `#B26A00` on `#FEF2E2`, sparkle.
- Verified: solid `#4EA26B` on `#ECFFF7`, check/edit.
- Rejected: solid `#D70015` on `#FFF0F1`, block.
- Deferred: solid `#8A94A6` on `#F3F6FA`, clock.
- Abstained: dashed `#8A94A6` on `#F3F6FA`, help.
- Conflict: solid `#D70015` on `#FFF0F1`, warning triangle.
- System: connected teal, syncing amber, offline grey.
- Workflow: neutral `#F3F6FA` on `#F3F6FA` with `lineStrong`, icon + label.
- `Semantics(label: 'Status: AI unverified')`, `excludeSemantics: true` on the visual children.

### 6.2 Panel

`Panel` = `DecoratedBox` white, 12 radius, 1 px `line`, optional 44 px header with `label` title and trailing widget, 1 px divider, content padding 20. No shadow. No nested panels. This replaces Material `Card` everywhere.

### 6.3 Data table

`DataTable` (Material) is acceptable for simple tables, but for dense product tables use a custom `DataTable`:
- Header on `surfaceSunken`, `label` 11/500, 40 px.
- Rows 40/44 px, 1 px divider, hover/selected states.
- Column alignments: text left, numbers right, status left.
- Sticky header inside a `Scrollbar` + `SingleChildScrollView`.
- Sortable headers: `Icon(Icons.arrow_upward/downward, 14)`; aria/semantics label.
- Empty state inside the panel, not a blank table.
- At 1280, hide low-priority columns into a row detail or overflow.

### 6.4 Metric strip

A single `Panel` with a `Row` of 5-6 `Expanded` segments separated by 1 px lines. Each segment 72-80 px, padding 16. Label 11/500 uppercase `ink3`; value 28/500 tabular; delta 12 px; optional sparkline 48x18. The first segment may have a 2 px accent underbar. No card grid, no gradient, no icon in a coloured circle.

### 6.5 Chart tooltip

240 px, white, 1 px `line`, 8 radius, 12 padding, overlay shadow only. Line 1: label; line 2: series with a 8 px dot + value + unit; line 3: comparison in `ink3`. No arrow, no blur.

### 6.6 Empty / loading / error

- `EmptyPanel`: 32 px icon `ink3` at 40% opacity, title 16/500, hint 13 px `ink2`, one primary or text action. 24 px padding, centered, max 360 px. One per region, not full screen unless the route is empty.
- `Skeleton`: `Container` 8 radius, `#EEF2F7`, opacity pulse 0.4-0.7 over 1.2 s. Static when `disableAnimations`. Shapes match the final content: metric strip 5 blocks, table header + 4 rows, chart axis + 8 bars, pane cards.
- `ErrorPanel`: `Icons.error_outline` red, title "Could not load [thing]", 1-line cause, `Retry` outline, optional `Details` expansion with the exception string. Inline, not a red page.
- `OfflineBanner`: 32 px, `surfaceSunken`, `cloud_off`, "Offline snapshot. Read-only until the local backend reconnects." + Retry. Every write button disabled with a tooltip. The dashboard still shows the last snapshot with an `Offline` pill.
- Toasts: `ZetaSnackBar` bottom center, 3 s, 1 action (`Undo` where applicable), no stacking more than 2.

### 6.7 Hash chip

`HashChip`: 11 px mono, `ink2`, `surfaceSunken` background, 4 radius, 4x6 padding, text `8f3a...c21d`, copy icon 12 on hover, `ZetaTooltip` with the full 64-char hash. Copy shows a toast "Hash copied". Never show the full hash in a table row.

### 6.8 Connection pill

`ConnectionPill`: 8 px dot + label 12 px + optional latency. Teal `#1A8080` for connected, amber `#B26A00` syncing, red `#D70015` error, grey `#8A94A6` offline. Dot pulses once on change. On hover: tooltip with endpoint and last sync. Used in the sidebar footer, top bar, and integrations card.

---

## 7. Role of the prototype

`deliverables/design/prototype/index.html` is a **static visual reference**, not production code. It implements the tokens and the eight screens at 1440 px so the Board and the Engineer can see the intended composition before Flutter work. It is:
- self-contained, no external fonts, no network, no libraries;
- not a source of truth for data or interaction (the Flutter app is);
- useful for pixel comparisons and for the "before/after" story.

Open it locally:
```
open deliverables/design/prototype/index.html
```
It has a fixed left index and a horizontal canvas. The frames are 1440x900; scroll or zoom to fit. The CSS variables mirror `design_tokens.json`.

---

## 8. Implementation guide for W7

### 8.1 File layout

```
lib/theme/tokens.dart                 K.* constants + applyLook(ThemeData)
lib/theme/zeta_theme.dart             ZetaProvider config + AppSemanticColors extension
lib/ui/shell/app_shell.dart           AppShell, AppSidebar, AppTopBar, RoleMenu
lib/ui/components/panel.dart          Panel, PageHeader, SectionTitle
lib/ui/components/status_pill.dart    StatusPill (all states), DashedBorderPainter
lib/ui/components/metric_strip.dart   MetricStrip, Metric
lib/ui/components/table.dart          DataTableShell, TableHeader, TableRow
lib/ui/components/state_views.dart    EmptyPanel, ErrorPanel, Skeleton, OfflineBanner, Kbd
lib/ui/charts/sparkline.dart          Sparkline (CustomPainter)
lib/ui/charts/recruitment_chart.dart  RecruitmentChart (CustomPainter)
lib/ui/charts/pr_bar.dart             PRBar
lib/ui/charts/regimen_gantt.dart      RegimenGantt
lib/features/login/                   LoginScreen
lib/features/dashboard/               DashboardScreen
lib/features/participant/             ParticipantListScreen, ParticipantScreen
lib/features/review/                  ReviewScreen + components
lib/features/audit/                   AuditScreen + ChainBadge + EventDetailPanel
lib/features/integrations/            IntegrationsScreen + SyncSteps
lib/features/quality/                 AiQualityScreen + PerFieldTable + Registry
lib/features/export/                  ExportScreen + StepTrail
```

The existing `app/lib/theme/tokens.dart`, `app/lib/ui/widgets.dart`, and the current screen files are a good base. Keep the names `K`, `Panel`, `PageHeader`, `Pill`, `Bar`, `Kbd`, `FadeIn` to avoid a second vocabulary. Extend them with `MetricStrip`, `StatusPill`, `DataTableShell`, `Skeleton`, `EmptyPanel`, `ErrorPanel`.

### 8.2 Theme code

Use `ZetaProvider(initialThemeMode: ThemeMode.light, initialContrast: ZetaContrast.aa, initialRounded: true)`, then apply `applyLook` to the Material theme. Keep `cardTheme` / `listTileTheme` unused by product screens; use `Panel` and custom rows.

The copy-ready extension is in `deliverables/design/tokens/zeta_theme_extension.dart`. It defines:
- `AppColors` (`ThemeExtension<AppColors>`) with all roles above.
- `AppType` with the type scale (IBM Plex Sans, weights 300/400/500).
- `AppSpace`, `AppRadii`, `AppMotion`.
- `buildYamiccTheme(ThemeData zetaBase)`.
- `StatusColors.of(context)` and `StatusPill` helpers.

Do not fork Zeta's `ZetaColors`. Use `Zeta.of(context).colors` for Zeta components, and `AppColors.of(context)` for product roles. They must agree on neutral surfaces; the accent is Zeta `mainPrimary`.

### 8.3 Data and state

- Use `repository.dart` for API data. Keep `models.dart` unchanged.
- Add view models for the new screens: `ConnectionStatus`, `SyncRun`, `SyncStep`, `EvaluationRun`, `FieldMetric`, `ModelEntry`, `ExportJob`, `ExportStep`, `ChainStatus`.
- The demo must work with the backend down: load the last snapshot and show `OfflineBanner` + read-only. Every write action checks `isOffline` and shows a tooltip.
- Use the fixed `demoToday` for all date logic.
- Do not show unverified AI values in the summary, completeness, export counts, or KPI "completeness". Only in the review queue and its counts.

### 8.4 Build order (suggested)

1. Theme extension + `Panel` / `StatusPill` / `DataTableShell` / `Skeleton` / `EmptyPanel` / `ErrorPanel`. Screenshot a component sheet.
2. Shell + sidebar + top bar + login. This changes the first impression immediately.
3. Dashboard metric strip + site table + queue card + recruitment chart.
4. Review three-pane rebuild with fixed action bar, evidence navigator, low-confidence sorting.
5. Audit table + chain badge + detail panel.
6. Participant workspace + timeline + Gantt.
7. Integrations + sync steps.
8. AI quality + export.
9. States, 1280 pass, keyboard pass, 200% pass, grayscale pass.
10. Before/after screenshots and a final comment.

### 8.5 Do not

- Do not use Material `Card`, `ListTile`, `Chip` defaults for product surfaces. They are the main reason v2 looked like a sample.
- Do not use Zeta `secondary` olive for buttons, progress, or selection.
- Do not use green for connection status or workflow status.
- Do not use a second blue. If a widget defaults to a different blue, override it or use the custom widget.
- Do not use the Zeta AI gradient except for a 16 px AI-running badge.
- Do not add `fl_chart`, `syncfusion`, or any chart package. Use `CustomPainter`; the charts are simple.
- Do not add a dark theme, a font, or a second family.
- Do not use `DateTime.now()` for demo logic.
- Do not animate page load, rows, or layout. Only state changes.
- Do not use modals for detail. Use inline panels or side sheets; dialogs only for confirm/irreversible/batch.
- Do not show raw exceptions to the user; use `ErrorPanel` with a `Details` expansion.
- Do not use more than 3 colours in a chart.
- Do not use icon-only navigation without labels in the expanded sidebar.

### 8.6 Performance and stability

- The charts are `CustomPainter` with `RepaintBoundary`; repaint only on data/hover change.
- Use `const` widgets and `ValueListenableBuilder`/`SelectableText` only where needed.
- Avoid rebuilding the whole page on a tick. The sync progress should update a small `ValueNotifier`.
- The app must start in under 2 s locally; if the backend is slow, show the shell + skeletons, not a blank screen.
- No network calls from the UI except the local API and localhost FHIR through the backend. The UI does not call FHIR directly.
- Keep the synthetic banner outside the scroll view so it never disappears.

---

## 9. Review checklist (QA and CEO)

Before marking W7 done, verify:

**Visual**
- [ ] Every screen uses `Panel`, not Material `Card`; no nested cards; no default `ListTile` rows.
- [ ] One accent (`#0073E6`), one AI amber, one verified green, one rejected red, one integrity teal. No olive.
- [ ] Type uses IBM Plex Sans 300/400/500 only; hierarchy is clear under the squint test.
- [ ] Numeric columns and metric values use tabular figures.
- [ ] The 12-col grid holds at 1440; 1280 has no horizontal scroll or clipped values.
- [ ] No page-load animation, no gradient decoration, no glassmorphism, no shadowed cards.
- [ ] The login, dashboard, review, audit, integrations, AI quality, and export all look like one product.

**Semantics and safety**
- [ ] AI vs verified vs rejected vs deferred is distinguishable in grayscale (dashed/solid, icon, label).
- [ ] Unverified values never appear in summary, completeness, exports, or KPI counts.
- [ ] Accept is disabled without evidence; conflict never overwrites silently; reject requires a reason.
- [ ] Every action writes one audit event with actor, source, before/after, model, prompt, timestamp.
- [ ] Chain badge verifies; broken/unavailable states exist; hashes are visible in the detail panel.
- [ ] Offline mode is read-only and every write action is disabled with a tooltip.
- [ ] Role differences are visible and enforced (nurse, monitor, PI).

**States and accessibility**
- [ ] Empty, loading, and error states exist for every panel and every new screen.
- [ ] Focus ring is visible on every interactive element; keyboard-only pass on review and audit.
- [ ] Contrast AA for all text and UI boundaries; the token table in §3.1 passes.
- [ ] 200% text scale: no clipped labels, no horizontal page scroll, actions remain reachable.
- [ ] Screen reader labels on status pills, confidence, evidence, charts (`Semantics` summary), and icon buttons.
- [ ] Reduced motion: skeletons static, evidence scroll instant, charts no animation.

**Demo**
- [ ] `make reset && make demo`, then the full 8-step story runs 3x without errors.
- [ ] Sync, extraction, review, audit verify, quality, and export update live from the backend.
- [ ] Backend-down test: shell loads, snapshot data, offline banner, read-only, retry works.
- [ ] 1440x900 and 1280x800 screenshots captured for every screen and attached to the ticket.
- [ ] `flutter analyze` clean; existing tests pass; new widget tests for `StatusPill`, `ChainBadge`, `MetricStrip`, `RecruitmentChart`, `ExportStepper`.

---

## 10. Appendix

### 10.1 Data used in the mock

- Study: `GBM-NL-2026-01`, ReDiReCT-GB demo, phase II.
- Participants: `GBM-NL-001..008`, 3 sites, synthetic.
- Extraction queue: 46 values, 2 abstained, 5 low confidence.
- Audit: 46 extract events + human decisions; chain demo 1,284 events.
- AI quality: rules provider, `demo-extractor-v0.3`, prompt `p-2026-11-07`, precision 0.94, recall 0.89, abstention 7%.
- Integrations: HAPI FHIR R4 at `http://localhost:8090/fhir`, 8 participants, 46 documents.
- Export: 8 participants, 46 documents, 1,284 observations, ODM / FHIR.

### 10.2 Open questions for the CEO / Engineer

1. Do we show the role switcher as a visible login feature or a hidden demo menu? This spec recommends visible role cards plus a footer role menu, so the Board can see the monitor read-only story in 5 seconds.
2. Does the audit chain have a real server-side hash in W1? The badge and detail panel assume `prevHash`, `hash`, `signature` fields. If not, show "chain metadata pending" rather than faking a hash.
3. Is the rules provider's output different enough from Ollama to make the provider switch visible? If not, show the same metrics with a "provider not available on this run" note rather than fake differences.
4. Should the export push write back to HAPI during the demo? It is a strong story; keep it behind a `Push to FHIR` action so a failure does not block the download.
5. Does the demo need a command palette? It is a "slick" signal, but it is optional; ship the `Ctrl/Cmd+K` shortcut to review if time is short.

### 10.3 Screenshot index

**v2 critique (captured from the committed build):**

| File | What it shows |
|---|---|
| `deliverables/design/critique/v2_dashboard_1440.png` | v2 dashboard: one card, empty canvas, Material defaults |
| `deliverables/design/critique/v2_participants_1440.png` | v2 participant list: full-width list, status chips |
| `deliverables/design/critique/v2_participant_1440.png` | v2 workspace: one column, no rail, no data-viz |
| `deliverables/design/critique/v2_review_1440.png` | v2 review: good three panes, four button styles, olive Correct |
| `deliverables/design/critique/v2_review_1280.png` | v2 review at 1280: wrapping value, wrapping buttons |
| `deliverables/design/critique/v2_audit_1440.png` | v2 audit: no columns, no chain badge, no detail |

**v3 visual reference (static prototype, not production):**

| File | What it shows |
|---|---|
| `deliverables/design/prototype/index.html` | All eight screens plus the state/component sheet, self-contained |
| `deliverables/design/prototype/shots/01_login.png` | Split login with three visible roles |
| `deliverables/design/prototype/shots/02_dashboard.png` | Metric strip, recruitment chart, queue, site table, alerts |
| `deliverables/design/prototype/shots/03_participant.png` | Timeline, Gantt, right rail, verified-only summary |
| `deliverables/design/prototype/shots/04_ai_review.png` | Three panes, evidence highlight, fixed action bar, collapsed rail |
| `deliverables/design/prototype/shots/05_audit.png` | Chain badge, dense table, prev/this/next hash detail |
| `deliverables/design/prototype/shots/06_integrations.png` | FHIR connection, sync history, step trace, mapping coverage |
| `deliverables/design/prototype/shots/07_ai_quality.png` | Per-field precision/recall, confusion matrix, model registry |
| `deliverables/design/prototype/shots/08_export.png` | Format cards, scope, validation, stepper, file tree |
| `deliverables/design/prototype/shots/09_states.png` | Status pills, empty, loading, error, offline, keyboard |

`deliverables/design/README.md` explains how to open the prototype and regenerate the screenshots.

### 10.4 Definition of done for this ticket

- `deliverables/D7b_visual_direction.md` committed.
- `deliverables/design/tokens/design_tokens.json` and `zeta_theme_extension.dart` committed.
- `deliverables/design/prototype/index.html` opens offline and shows the eight screens.
- `deliverables/design/critique/*.png` committed.
- A comment on CEL-1775 with the commit hash, the commands used, the screenshots, and the open questions above.
- W7 can implement without guessing: every screen has a layout, widget names, token values, states, and acceptance criteria.
