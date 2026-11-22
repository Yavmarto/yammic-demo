# D7c — v4 screens: five new features in the v3 visual language

**Owner:** Designer · **For:** Engineer (F), CTO (D), PM, QA · **Date:** 2026-11-21
**Status:** implementation spec on branch `v4` · **Due:** Sun 2026-11-22 09:00 CET
**Read first:** `deliverables/D7b_visual_direction.md` (the visual contract), `app/lib/theme/tokens.dart` (live tokens), `deliverables/design/w7_after/` (v3 screenshots).
**Reference frames:** `deliverables/design/v4/index.html` and `shots/` (same tokens, same shell).
**Source data:** `deliverables/protocol_GBM-NL-2026-01_synopsis.md`, `deliverables/protocol_criteria.json`.

This document adds **only** what is new. Everything in D7b still applies: Panel not Card, borders not shadows, IBM Plex Sans 300/400/500, accent `#0073E6`, the AI/verified/integrity colour grammar, 4/8/12/16/24/32/48 spacing, 40 px targets, 12.5 px small text, tabular numbers, no dark mode, no page-load choreography, synthetic banner on every screen.

Sections 1 and 3 are released first so the Engineer can start. Sections 2, 4 and 5 follow in the same file before 09:00. Because of that release order, §3 appears before §2 in this file; the numbering follows the task, not the reading order.

---

## 0. Shared changes

### 0.1 Routes and navigation

| Route | Screen | Nav group | Roles |
|---|---|---|---|
| `/screening` | Screening queue + checklist | STUDY · **Screening** (badge = to screen) | nurse, PI (sign off); monitor read |
| `/participants/:id` | Participant workspace, tab **Overview** | Participants | all |
| `/participants/:id/timeline` | Participant timeline tab | Participants | all |
| `/queries` | Queries inbox, role-aware | STUDY · **Queries** (badge = open) | monitor, nurse, PI |
| `/protocol` | Protocol → form builder | PLATFORM · **Protocol → form** | PI (approve); others read |

- New nav items use the existing 40 px item: 12 px icon + 14 px label. `Screening` icon `fact_check_outlined`; `Queries` `forum_outlined`; `Protocol → form` `account_tree_outlined`. Badges use the existing neutral tag with an amber dot when >0.
- Keep route transition 120 ms fade. `main.dart` switch adds the four routes; `/participants/` parsing must accept `/participants/<id>/timeline`.
- Breadcrumbs: `Screening / <candidate>`, `Queries / #Q-014`, `Participants / GBM-NL-001 / Timeline`, `Protocol / GBM-NL-2026-01`.

### 0.2 Role change (important)

v3 made the monitor fully read-only. v4 needs the monitor to **raise queries and tick source verification**, while the eCRF stays read-only.

| Action | Nurse | Monitor | PI |
|---|---|---|---|
| View all screens | yes | yes | yes |
| Sign off screening decision | yes | no | yes |
| Raise query | no (replies) | **yes** | yes |
| Reply / resolve query | yes | no (waits) | yes |
| Mark source verified (SDV) | no | **yes** | no |
| Accept/correct/reject AI values | yes | no | yes |
| Analyse protocol / edit proposals | no | no | yes |
| Approve form version | no | no | **yes** |

- Replace the shell `_ReadOnlyBanner` with `Monitor banner`: `Monitor · queries and source verification only. The eCRF is read-only.` (`K.infoBg`, `Icons.visibility_outlined`, 13 px `K.infoInk`).
- `WriteGate` reasons updated: nurse SDV → `Source verification is a monitor action.`; non-PI approve → `Only the PI can approve a form version.`; monitor reply → `Monitor waits for the site to answer.` Keep blocked actions visible with a tooltip.
- Every write action is audited with actor, role, time, before/after where applicable.

### 0.3 Shared widgets to add

Add to `app/lib/ui/v4_widgets.dart` (feature screens import it; do not duplicate):

| Widget | Job |
|---|---|
| `ScopeBar` | Site scope chips + compare affordance for the dashboard |
| `StatePill` | Finding/verification pill: `met`, `notMet`, `unknown`, `ai`, `verified`, `planned`, `screenFail`, `eligible`, `open`, `answered`, `resolved` |
| `EvidenceLink` | 16 px link icon + `DOC-001-PATH · p.2 ¶3`; opens `DocumentDialog`, never navigates away |
| `EvidenceBox` | Quote with the v3 highlight `#FFE1A8`, 2 px `K.aiLine` bottom rule, source meta line |
| `ThreadBubble` | Quiet message row: avatar 24, name/role/time, body, attachment chip. Not a coloured chat bubble |
| `SDVTick` | Monitor-only source-verified control; green `verified_user` pill when done, with actor + time |
| `SectionTabs` | Underlined 40 px tabs for participant Overview / Timeline / eCRF / Queries |
| `VersionPill` | `Active`, `Draft`, `Superseded` version state |
| `EmptyState`, `ErrorState`, `Panel`, `Pill`, `Skeleton`, `Kbd` | Reuse from `app/lib/ui/widgets.dart` |

Reuse `Tone`: `ok` (human verified), `ai` (AI / attention), `bad` (not met, conflict, screen-fail), `info` (selected/answered), `muted` (unknown/resolved/planned). Teal `K.teal` stays system integrity only.

### 0.4 API assumptions (D owns the final shape)

| Feature | Proposed calls |
|---|---|
| Screening | `GET /screening?status=to_screen`, `GET /screening/{participantId}`, `POST /screening/{participantId}/criteria/{code}` `{state}`, `POST /screening/{participantId}/signoff` `{decision, reason?}` |
| Sites | `GET /studies/{id}/dashboard?site=SITE-02`, `GET /studies/{id}/sites/compare?ids=SITE-01,SITE-02` |
| Queries | existing `GET /queries?status=open|closed|answered`, `POST /queries`, `POST /queries/{id}/reply` `{text}`, `POST /queries/{id}/close` `{note?}`, `POST /participants/{id}/ecrf/{field}/sdv` |
| Timeline | `GET /participants/{id}/timeline` |
| Protocol | `GET /protocols/{id}`, `POST /protocols/{id}/analyze`, `GET /protocols/{id}/proposals`, `POST /studies/{id}/form-versions` `{criteria[], fields[], note?}` |

Until D lands, screens may read the bundled synthetic JSON behind `Loader` and keep the same widget contract.

---

## 1. Screening queue + criteria checklist

**Job:** a coordinator sees every referred patient, checks each entry criterion against the source, and signs one clear decision: **eligible**, **screen-fail**, or still in screening. The AI proposes criterion states with evidence; only a human sign-off moves the patient.

**Route:** `/screening` (queue) and `/screening/:participantId` (selected). Selection may be inline at ≥1280.

### 1.1 Layout (1440)

```
┌ PageHeader: Screening            [Site: all v] [Sync]                    ┐
│ 3 to screen · 1 awaiting sign-off · 1 screen-fail                         │
├──────────────────┬───────────────────────────────────────────────────────┤
│ QUEUE 360        │ CHECKLIST                                             │
│ [To screen|Sign-off|Screen-fail|All]                                    │
│ search + severity                                                       │
│ ┌──────────────┐ │ GBM-NL-004  [Screening]   9 met · 1 not met · 3 unknown│
│ │ GBM-NL-004   │ │ 44 y · F · Site 02 · referred 21 Nov   [Sign off ...]│
│ │ 9/13 · 3 ?   │ │ Source: DOC-201-PATH, DOC-201-MRI, DOC-201-DIS       │
│ └──────────────┘ │ ┌ INCLUSION (9) ───────────────────────────────────┐ │
│ ...              │ │ ✓ INC-01  Age ≥18 y            Met    [evidence]│ │
│                  │ │ ✓ INC-02  Histology ...        Met    [evidence]│ │
│                  │ │ ⨯ INC-03  MGMT status known    Not met[evidence]│ │
│                  │ │ ? INC-05  Bone marrow          Unknown[evidence]│ │
│                  │ └──────────────────────────────────────────────────┘ │
│                  │ ┌ EXCLUSION (4) ───────────────────────────────────┐ │
│                  │ │ ✓ EXC-01  Prior brain RT       Met (none)      │ │
│                  │ └──────────────────────────────────────────────────┘ │
│                  │ [8 human-confirmed · 3 AI only · 2 unresolved]        │
└──────────────────┴───────────────────────────────────────────────────────┘
```

- At ≥1280: queue 360 fixed + 16 gap + checklist flex. Page padding 24.
- At 1024–1279: queue 320; checklist scrolls horizontally never; criteria text wraps to 2 lines max, then tooltip.
- At <1024: single pane; queue first, selecting a candidate pushes the checklist with a back chevron. Do not show both.
- Queue panel `Panel(padding: EdgeInsets.zero)`. Header 44 px: `label` + count. Filter segmented control 32 px, then search field 40 px, then site chip row.
- Queue row 64 px: ID 14/500 tabular; line 2 `44 y · F · Site 02 · referred 21 Nov` 12.5 `K.ink3`; right: `9/13` 12.5 mono and a 4 px stacked bar (met green, not met red, unknown grey, undecided `K.line`); status pill below. Selected: `K.accentSoft` + 2 px `K.accent` left rule is **not** used; use a 2 px `K.accent` border with 11 px radius and `K.accentSoft` fill. Hover `K.bg`.
- Status pills: `Screening` `Tone.info`, `Awaiting sign-off` `Tone.ai`, `Eligible` `Tone.ok` (`check_circle_outline`), `Screen-fail` `Tone.bad` (`person_off`). Screen-fail is an outcome, not an error: keep the label and icon, never a red row background.

### 1.2 Checklist

Header block inside the panel, 88 px: ID `K.title` + status pill; meta line 12.5 `K.ink2`; right `Sign off eligibility` `FilledButton` (disabled until 1.4). A 160 px progress bar 4 px + `8 of 13 confirmed` 12 px below. Source chips 28 px, neutral `Pill` with `Icons.description_outlined`, click opens the document dialog.
- Group headers sticky 32 px on `K.sidebar`, `K.label` uppercase + count. Order: inclusion, exclusion.
- Criterion row min 56 px, 1 px `K.line` divider, 16 px horizontal padding:
  - Status icon 18: met `check_circle_outline`, not met `block`, unknown `help_outline`; colour follows verification (1.3).
  - Code 52 px mono 12 `K.ink2`.
  - Text 14/1.45 `K.ink`, max 2 lines; criterion ID is the keyboard label.
  - State pill `StatePill` 10.5/500.
  - Evidence `EvidenceLink` 12 `K.infoInk`; if no span, `No evidence` muted + `Icons.link_off`.
  - Overflow `⋯` 32 px: `Confirm met`, `Confirm not met`, `Mark unknown`, `Open source`, `Raise query` (monitor only).
- Row expands inline (180 ms, no modal): `EvidenceBox` with the exact protocol/report excerpt (max 68ch), source meta `DOC-201-MRI · p.2 ¶3 · received 21 Nov 2026`, and the AI rationale in 12.5 `K.aiInk`: `AI: KPS 70 recorded 18 Nov, within 7 days. Confidence 0.91.` Actions: `Confirm met` primary, `Confirm not met` outline, `Mark unknown` text.
- Selecting a row scrolls the source highlight into view when the source pane is open (document dialog), 200 ms; respect reduced motion.

### 1.3 State grammar (the safety rule)

A criterion has **finding** and **verification**; both must be visible.

| Finding | AI proposal (unverified) | Human confirmed |
|---|---|---|
| Met | `Tone.ai` pill, dashed 2 px `K.aiLine`, `auto_awesome`, label `Met · AI` | `Tone.ok` pill, solid 2 px `K.okLine`, `check_circle_outline`, label `Met` |
| Not met | `Tone.ai`, dashed, `auto_awesome`, `Not met · AI` | `Tone.bad`, solid, `block`, `Not met` |
| Unknown | `Tone.muted`, dashed, `help_outline`, `Unknown · AI` | `Tone.muted`, solid, `help_outline`, `Unknown` |
| No data | `Tone.muted`, dashed, `link_off`, `No evidence` | same, text `Not assessable` |

- Confirm actions are human writes: they change the pill to the solid verified form and write one audit event (`screening.criterion.confirm`, before/after).
- AI cannot sign off. An all-AI checklist shows `AI proposals only · 0 human-confirmed` in `K.aiInk`; Sign off is disabled.
- `Unknown` never displays as met. Do not auto-fill `Not met` when evidence is missing.

### 1.4 Sign-off

`Sign off eligibility` opens `SignOffDialog` (480 px, 16 radius, 1 px `K.line`, shadow allowed):
1. Summary: `9 met · 1 not met · 3 unknown`; a 4 px stacked bar; `3 criteria need a human decision` in `K.aiInk` if any.
2. Decision cards 2-up: `Eligible` (`check_circle_outline`, green when selected) / `Screen-fail` (`person_off`, neutral when selected; never red fill).
3. `Screen-fail reason` dropdown, required for fail: `Did not meet inclusion criteria`, `Met an exclusion criterion`, `Withdrew consent`, `Other`. Free text 120 chars for Other.
4. Checkbox `I checked every criterion against its source.` required.
5. `Sign off` primary (disabled until valid) + `Cancel` outline. On submit, spinner in the button, then close.
- After success: `ZetaInPageBanner`-style inline green panel at the top of the checklist: `Eligible · signed off by SYN-JD at 14:12` + `Open participant` link + `View audit event`. The queue row moves to `Awaiting sign-off` → `Eligible`; the button becomes `Signed off` disabled. No confetti, no modal result.
- Screen-fail also writes the participant `statusDetail = screen_failed` with the reason; keep the data visible and read-only.
- Re-sign requires an explicit `Reopen screening` in the overflow (PI only), with a reason; audit event.

### 1.5 States

| State | Rendering |
|---|---|
| Empty queue | `EmptyState(Icons.fact_check_outlined, 'No candidates to screen', 'Sync hospital data or add a referral to start screening.')` + `Sync now` |
| No criteria | `EmptyState(Icons.rule_outlined, 'No approved criteria', 'The PI must approve a protocol form version before screening.')` + `Open protocol` |
| No source span | Row shows `No evidence`; expanded row says `No evidence span. Confirm manually or request the source document.`; evidence action disabled with tooltip |
| Loading | Queue: 6 skeleton rows at 64 px. Checklist: header skeleton + 8 skeleton criterion rows; no full-page spinner |
| Error queue | Inline `ErrorState('Screening queue unavailable. ...', Retry)`; keep the last list with an `Offline` pill if cached |
| Error checklist | `ErrorState` inside the checklist panel; queue stays usable; Retry reloads the selected candidate only |
| Offline | Global banner + `Offline snapshot` pill; Sign off, Confirm and Reopen disabled with `Reconnect the local backend to write.`; evidence and documents remain readable |
| Sign-off conflict | If another user signed off first (409), banner `This candidate was signed off by SYN-AB at 14:05. Reload to see the decision.` + Reload |

### 1.6 Widgets and acceptance

**Widgets:** `ScreeningQueueScreen`, `ScreeningQueuePanel`, `ScreeningFilterBar`, `ScreeningQueueRow`, `CriteriaChecklist`, `CriteriaGroupHeader`, `CriterionRow`, `StatePill`, `EvidenceLink`, `EvidenceBox`, `SignOffDialog`, `ScreeningSignOffBanner`, `EmptyState`, `ErrorState`, `Skeleton`.

**Acceptance**
- A candidate can be screened end to end: select → confirm criteria → sign off → queue updates → audit event exists.
- Sign off is impossible with an AI-only or unknown criterion; the reason is visible via tooltip.
- Every criterion shows finding + verification, icon + text + shape; grayscale still distinguishes all states.
- Evidence opens the exact source excerpt; no evidence is never silently accepted.
- Empty/loading/error/offline states above are implemented; 200% text does not clip the code or pills.
- Keyboard: `Up/Down` queue, `Enter` select, `Tab` through criteria, `M` met, `N` not met, `U` unknown when a row has focus; no single-letter shortcuts while a text field has focus.

---

## 3. Data-quality / queries inbox

**Job:** the monitor questions a value and the nurse answers it; the monitor can also tick that a value was checked against the source (SDV). One thread per field, not a chat app.

**Route:** `/queries`. Entry points: nav badge; participant eCRF row overflow `Raise query`; dashboard `Open queries`; participant `Queries` tab.

### 3.1 Layout (1440)

```
┌ PageHeader: Queries       [Open|Answered|Resolved|All] [Severity v] [Site v]  [Ask a query] ┐
│ Monitor: questions you asked the sites. Nurse: questions from the monitor.                │
├─────────────────────┬───────────────────────────────────┬───────────────────────────────┤
│ QUERY LIST 360      │ THREAD                            │ FIELD CONTEXT 340             │
│ ● KPS · GBM-NL-002  │ #Q-014 · KPS · GBM-NL-002         │ Field · KPS                   │
│   "KPS 80 in eCRF…" │ [Open]  [High]        [SDV tick]  │ eCRF value   80 %             │
│   1 d · Site 01     │ ───────────────────────────────   │ Source value 70 %             │
│                     │ MV · Monitor · 21 Nov 10:12       │ [Conflict] values differ      │
│   KPS · GBM-NL-003  │ Please confirm which KPS…         │ Evidence: DOC-... · p.1 ¶4    │
│   "Source says…"    │                                   │ [Open source]                 │
│                     │ JD · Nurse · 21 Nov 10:40         │ ───────────────────────────── │
│                     │ Source says 80 on 20 Nov…         │ History: 2 messages           │
│                     │ [DOC-201-DIS · p.1]               │ Audit: 4 events               │
│                     │ ───────────────────────────────   │                               │
│                     │ [Reply…                    ] Send │                               │
│                     │ [Resolve query]                   │                               │
└─────────────────────┴───────────────────────────────────┴───────────────────────────────┘
```

- Page padding 24, panel gap 16. Three panels fill the height; each body scrolls independently.
- At 1024–1279: list 320 + thread; field context becomes a collapsible `Field context` section at the top of the thread (44 px header, expandable to 260 px), because the third pane would squeeze the thread.
- At <1024: single column: list → thread (with back chevron); field context always below the thread.
- No page-level scroll on this screen. The composer is fixed to the bottom of the thread panel.

### 3.2 Query list

- Header 44 px `label` + count; filter row 40 px: `SegmentedButton` `Open / Answered / Resolved / All`, severity `DropdownButton` (`All`, `High`, `Medium`, `Low`), site dropdown (shared site list), search 220 px. Counts per segment 11 px `K.ink3`.
- Row 72 px, 1 px divider, hover `K.bg`, selected `K.accentSoft` + 2 px accent border (same as 1.1, no side stripe):
  - Line 1: severity icon 16 (high `error_outline` `K.badLine`; medium `warning_amber_rounded` `K.aiLine`; low `info_outline` `K.infoLine`), field label 13/500, right age `1 d` mono.
  - Line 2: question snippet 12.5 `K.ink2`, max 1 line ellipsis; line 3: `GBM-NL-002 · Site 01` 11.5 `K.ink3` + status pill `Open` `Tone.ai`, `Answered` `Tone.info`, `Resolved` `Tone.muted` (`check`).
  - Unread: 6 px accent dot at the right; `Semantics(label: 'Unread reply')`.
- Monitor sees `Open` and `Answered` groups by default, newest first; nurse sees their site's open queries first, unanswered oldest first.
- List footer: `9 open · 2 answered · 18 resolved` 12 `K.ink3`.

### 3.3 Thread

- Thread header 64 px: `#Q-014` mono + field `KPS` 15/500 + participant link (accent); status pill; severity pill; right `SDVTick` (monitor only). Below: `Raised 21 Nov 10:12 · Site 01 · FUMC Zuidhaven` 11.5.
- Messages: `ThreadBubble` rows with 24 px avatar, name + role + time (`MV · Monitor · 21 Nov 10:12`), body 14/1.5 max 68ch, optional attachment chip `DOC-201-DIS · p.1` with `Icons.attach_file` and `Open source`. No bubble fills, no left/right alignment: quiet vertical thread with 1 px connectors.
- System row: `JD marked the query answered · 21 Nov 10:40` 11.5 `K.ink3`, `Icons.check`.
- First message uses `K.surface`; replies use `K.surface`; the resolved banner uses `K.infoBg`: `Resolved by JD · 21 Nov 11:02. Source verified.` with an audit link.
- Composer 84 px: focused `TextField` 3 lines max, placeholder `Reply to the site…`; helper `Do not paste patient identifiers.` 11 `K.ink3`; `Send reply` primary 40 px. Nurse/PI also see `Resolve query` outline, which opens a 420 px confirm dialog: optional `Resolution note` (200 chars), `Resolve` primary. On success the thread gets the system row and the composer becomes read-only `Query resolved. Reopen from the monitor is required.`
- Monitor cannot reply or resolve (role rule); composer is read-only with `Waiting for the site to answer.` and a copy of the first message. They can still add a query from the header.
- `Raise a query` dialog (monitor and PI): Participant (required), Field (optional dropdown of eCRF fields), Severity segmented Low/Medium/High, Question (required, 500 chars), `Send query`. Prefill participant/field when launched from an eCRF row. After send, select the new thread and clear the list filter if needed.

### 3.4 Field context and SDV

- Panel header `Field context` + `eCRF · ECRF-GBM-BASELINE` 11 `K.ink3`.
- Value compare block: eCRF value 24/500 tabular + unit; label `eCRF value`; source value 24/500; label `Source value`. If equal: `Source agrees` `Tone.ok` with `check`. If different: a `Conflict` `Tone.bad` banner (red surface, solid 2 px) `Values differ. The query asks the site to confirm which value is correct.` Both values stay visible; never auto-resolve.
- Evidence: `EvidenceBox` + `EvidenceLink`; `Open source` outline 40 px opens the existing document dialog with the span highlighted. If no span: `No evidence attached. The monitor can attach one from the source document.`
- `SDV tick`:
  - Unverified: outlined 40 px `Mark source verified` with `verified_user_outlined`, monitor only. Disabled for nurse/PI with tooltip `Only the monitor can verify the source.`; disabled offline.
  - Verified: green `Tone.ok` `Pill('Source verified · MV · 21 Nov 14:12', icon: Icons.verified_user)`; below `SDV is append-only in this demo.` 11 `K.ink3`. Writes `ecrf.sdv` audit with participant, field, actor, timestamp.
  - The dashboard `SDV done / pending` counts update after the write; the participant eCRF row shows `SDV done` (existing pill).
- History block: `2 messages · 4 audit events` with `View audit filtered` link.
- If the field has an open AI proposal, add `AI · Unverified` amber note `This field also has an unreviewed AI proposal. Review it in the AI queue.` — do not mix query state with AI state.

### 3.5 States

| State | Rendering |
|---|---|
| Empty list (role) | Monitor: `EmptyState(Icons.forum_outlined, 'No open queries', 'Raise a query from a participant field when a value needs a source check.')` + `Open participants`. Nurse: `'No questions for your site'` + `View resolved` |
| No selection | Thread panel `EmptyState(Icons.chat_bubble_outline, 'Select a query', 'Open a query on the left to read the thread and answer it.')`; field context shows a quiet placeholder, not empty boxes |
| Empty thread replies | `Waiting for the site to answer.` + `Raise date`; no fake messages |
| Loading | List 6 skeleton rows 72 px; thread header skeleton + 3 message skeletons; field context 128 px skeleton; no full-page spinner |
| Error list | `ErrorState('Queries unavailable. The local backend did not answer.', Retry)`; keep cached list with `Offline` pill |
| Error send | Snackbar `Could not send the reply: <reason>. Your text is kept.` Keep the typed text; do not clear the composer |
| Error SDV | Snackbar + keep unverified; never show the green tick before the server confirms |
| Offline | Read-only banner; compose/send/resolve/SDV disabled with tooltip `Reconnect the local backend to write.`; threads readable |
| 409 on SDV/close | Inline banner `This query changed since you opened it. Reload to see the latest.` + Reload |

### 3.6 Widgets and acceptance

**Widgets:** `QueriesScreen`, `QueryFilterBar`, `QueryList`, `QueryRow`, `QueryThread`, `ThreadBubble`, `QueryComposer`, `ResolveQueryDialog`, `RaiseQueryDialog`, `FieldContextPanel`, `ValueCompare`, `SDVTick`, `EvidenceLink`, `EvidenceBox`, `EmptyState`, `ErrorState`, `Skeleton`.

**Acceptance**
- Monitor can raise a query on a field, nurse can reply and resolve, monitor can tick SDV; all three actions appear in the audit trail with actor/role/time.
- The same query appears with the correct view for each role; no write action is hidden without a tooltip reason.
- `Open / Answered / Resolved` filters, severity and site filters, and search compose correctly; counts update after a write.
- Conflict is never auto-resolved; both values visible; SDV cannot be set by nurse/PI or offline.
- Composer preserves text on error; thread stays readable at 200% text; no horizontal scroll at 1280.
- Empty/loading/error/offline states above exist; grayscale still distinguishes open/answered/resolved and SDV.

---

## 2. Site switcher + site comparison on the dashboard

**Job:** the PI sees one site or the whole study in the same dashboard, and can compare two or three sites without exporting anything. The scope must be obvious, never a hidden filter.

**Route:** `/` (dashboard) with an in-memory `siteId` scope (`all` default). Optional deep link `/?site=SITE-02`; keep the scope for the session only.

### 2.1 Dashboard header changes

- PageHeader subtitle becomes scope-aware: `ReDiReCT-GB · All sites · 3 sites · last sync 2 min ago` or `Site 02 · FUMC Noordhaven · last sync 2 min ago`.
- Trailing actions, 40 px:
  1. `SiteScope` dropdown (`MenuAnchor`/`ZetaDropdown`, 240 px): `All sites` + one row per site. Row: 8 px dot (teal connected, grey offline), `FUMC Noordhaven`, `Site 02`, right `3/8 enrolled`. Selected row `K.accentSoft` + check.
  2. `Compare sites` `OutlinedButton.icon(Icons.compare_arrows)`; disabled with tooltip `This study has only one site.` if <2 sites.
  3. `Refresh` outline (existing).
- The dropdown trigger is a 40 px outlined control `All sites` + chevron; when scoped, it shows `Site 02 · Noordhaven` in `K.ink` 500 and a small `Scope` label above? No: keep one line; the page subtitle carries the explanation.
- Changing scope: 180 ms fade of the metric strip and panels, no layout jump; announce `Dashboard filtered to Site 02, FUMC Noordhaven.` via `SemanticsService.announce`. Keep scroll position.
- Do not change the top context bar into a second site switcher; the top bar keeps `GBM-NL-2026-01` and `Data as of 23 Nov 2026`. One scope control only.

### 2.2 Scoped dashboard

- Metric strip labels gain a scope suffix: `Enrolled` → `Enrolled · Site 02`; values are site-only. Never mix global and site numbers in one strip.
- Recruitment chart: same components, site-only series; title `Recruitment · Site 02`; target label `Site target 8`. When `All sites`, add a thin `Site 01 / 02 / 03` segmented legend above the chart as direct labels, not a rainbow.
- Site performance table: when scoped, dim the other rows to 45% opacity and show a `Viewing` pill (`Tone.info`) on the active row; clicking another row switches scope (one click, no menu).
- A small `Showing Site 02` `Pill(Tone.info, Icons.filter_alt_outlined)` + `Show all sites` text link appears under the header whenever scope ≠ all.
- AI queue and tasks remain global in this demo; label them `All sites` in the panel header to prevent a false assumption. Open queries in the metric strip are scoped; the queries inbox stays global.

### 2.3 Site comparison panel

Placed directly below the metric strip, full width, `Panel`. Only when `All sites` is selected; hidden when a single site is scoped (the scoped table is the comparison there). Height 300 px at 1440, no page scroll below 900 if possible.

```
┌ Site comparison                              [Compare: ☑ 01 ☑ 02 ☑ 03]  ┐
│ 12-column grid: 8 col grouped bars, 4 col summary                       │
│ Enrolment vs target   ▇▇ 3/10  ▇▇▇ 3/8  ▇▇ 2/6                          │
│ eCRF completeness     ▇▇▇ 70%  ▇▇▇ 78%  ▇▇ 64%                          │
│ Open queries / pt     ▇ 1.3    ▇ 1.0    ▇ 1.0                           │
│ SDV coverage          ▇▇ 40%   ▇▇▇ 55%  ▇▇ 50%                          │
│                                                                          │
│ Site        Enrolled  Screening  Queries  eCRF  SDV   Last sync  Δ avg  │
│ 01 Zuidhaven  3/10      4          4      70%  40%    2 min      -3 pp   │
│ 02 Noordhaven 3/8       5          3      78%  55%    2 min      +5 pp   │
│ 03 Westpark   2/6       2          2      64%  50%    2 min      -9 pp   │
└──────────────────────────────────────────────────────────────────────────┘
```

- Compare chip row: 3 site chips 32 px with a 16 px checkbox, site short name, dot. At least 2 selected; the third may be unchecked. Disabled all-unchecked state: `Select at least two sites.`
- `SiteBars` (`CustomPainter`): one row per metric, grouped bars 8 px wide, 4 px gap, 12 px group gap; bar fill = `K.accent` at 18% with a 2 px solid `K.accent` cap? Use one colour per metric (`chart1`, `chart2`, `chart3`, `chartMuted`) and **direct labels** at the bar end (12 px tabular `K.ink2`). No legends for site identity inside each row; the row label is the metric, the site order is fixed (01/02/03) and labelled once in the header.
- Table below, 40 px rows, sticky header `K.label` on `K.sidebar`:
  - Columns: Site (flex, short name + `Site 0X` 11 px `K.ink3`), Enrolled (88 right), Screening (80 right), Queries (72 right), eCRF (96: value + 48 px bar), SDV (96: value + 48 px bar), Last sync (88 mono), Δ vs study avg (80 right).
  - Δ: `+5 pp` in `K.tealInk` (positive is teal, never green) and `-3 pp` in `K.badInk`; arrow icon 12 + number, not colour alone.
  - Row click scopes the dashboard to that site (`SiteScope` updates); hover `K.bg`; keyboard Enter does the same.
- A 12 px note under the table: `Delta is the site value minus the study average. Enrolment is site-only.` Honest definition, no orphan numbers.
- Comparison panel is read-only for all roles, including monitor.

### 2.4 States

| State | Rendering |
|---|---|
| One site | Panel replaced by `EmptyState(Icons.compare_arrows, 'Comparison needs two sites', 'This study has one site. The dashboard shows its numbers directly.')` |
| No data | `EmptyState(Icons.bar_chart, 'No site data yet', 'Sync a hospital connection to load site metrics.')` + `Open integrations` |
| Less than 2 selected | Bars and table dim 40%; note `Select at least two sites to compare.`; no error colour |
| Loading | Header skeleton 240 px + 4 grouped-bar skeleton rows + 3 table skeleton rows; metric strip uses its own skeletons |
| Error | Keep the last comparison with an inline `ErrorState('Comparison unavailable. Showing the last snapshot.', Retry)` above the table; do not blank the panel |
| Offline | `Offline snapshot` pill; last numbers with `Data as of 14:02`; no disabled buttons (all read-only) |
| Site off / paused | Site row shows neutral `Paused` pill; include it in bars at 45% opacity and label `Paused`; do not hide it silently |

### 2.5 Widgets and acceptance

**Widgets:** `DashboardScreen` (extend), `SiteScope` (dropdown), `SiteScopeBar`, `ScopedMetricStrip`, `SiteComparisonPanel`, `CompareSiteChips`, `SiteBars` (`CustomPainter`), `SiteCompareTable`, `DeltaBadge`, `EmptyState`, `Skeleton`, `Panel`.

**Acceptance**
- Switching `All sites` ↔ one site updates every scoped number and the subtitle; no global number appears under a site label.
- Comparing 2 or 3 sites works from the dashboard only; unchecking below 2 is blocked with a clear note; row click scopes.
- Bars and table agree; deltas are computed against the study average and use teal/red with arrows and text.
- 1280 shows the panel without horizontal scroll; labels do not collide; 200% text wraps and the panel scrolls.
- Empty/loading/error/offline states above; comparison is read-only for monitor.

---

## 4. Participant timeline

**Job:** one line of the patient's treatment history — surgery, radiotherapy, chemotherapy cycles, scans and visits — where every event opens its source document. It replaces the visit-only rail as the main history view, but keeps the visit detail.

**Route:** `/participants/:id/timeline`, or the **Timeline** tab on the participant workspace. Deep links from the Overview visit rail, dashboard alerts and queries open this tab with the event selected.

### 4.1 Participant tabs

- Add `SectionTabs` under the participant PageHeader: `Overview`, `Timeline`, `eCRF`, `Queries (n)`. 40 px tall, 1 px bottom border `K.line`, active tab 2 px accent underline + `K.ink` 500; inactive `K.ink2` 400. No pills.
- Keep the participant header (ID, status pill, age/sex/site, consent, `Review AI (n)`) on every tab. The right actions stay the same.
- `Overview` is the existing workspace. `Timeline` is the new full-width screen. `eCRF` scrolls to the existing eCRF panel (or shows it alone at <1100). `Queries` filters the inbox by participant.
- Timeline tab preserves the back route; browser/back returns to Overview.

### 4.2 Layout (1440)

```
┌ GBM-NL-001 [Active] 57 y · F · Site 01 · consent active   [Review AI (3)] ┐
│ [Overview] [Timeline] [eCRF] [Queries (2)]                              │
├──────────────────────────────────────────────────────┬──────────────────┤
│ TIMELINE   [3M] [6M] [All]   Surgery RT Chemo Scans  │ EVENT            │
│ Jun        Jul        Aug        Sep        Oct   Nov │ Surgery          │
│ ─┬─────────┬──────────┬──────────┬──────────┬─────┬─ │ 01 Jun 2026      │
│ S│ ● craniotomy (GTR)                                │ Gross total      │
│ R│            ▭▭▭▭▭▭▭▭ 60 Gy / 30 fx                 │ resection        │
│ C│              ▲1 ▲2 ▲3 ▲4 ▲5 ▲6 (planned)          │ [Verified]       │
│ M│      ◆ baseline   ◆ post-op   ◆ W6   ◆ W12        │ Source           │
│ V│ ● V0  ● V1  ● V2  ● V3  ● V4 ... ● V8            │ DOC-001-OP · p.1 │
│                                                      │ "Gross total     │
│ legend: ● event  ▭ interval  ◆ scan  ┆ today         │  resection..."   │
│                                                      │ [Open source]    │
│                                                      │ ───────────────  │
│                                                      │ All events (14)  │
└──────────────────────────────────────────────────────┴──────────────────┘
```

- Page padding 24. Timeline panel flex 8, event rail 4 (360 px at 1440), 16 gap. Timeline panel height fills the viewport minus header/tabs; inner horizontal scroll only if zoom requires it (never at 1440 for 6M).
- At 1024–1279: event rail becomes 300 px; lane label 96 px; timeline still fits 6M.
- At <1024: timeline becomes a **vertical** grouped list (same `TimelineEvent` rows, no horizontal axis), event panel is a bottom sheet on tap. This is the accessibility fallback, not a degraded afterthought.

### 4.3 Time axis and lanes

- Header row 32 px: `3M / 6M / All` `SegmentedButton` 32 px (default `6M`), lane toggle chips `Surgery`, `Radiotherapy`, `Chemotherapy`, `Scans`, `Visits` (all on by default), right `Today · 23 Nov 2026` 11.5.
- Axis: month labels `Jun … Dec` 11 px `K.ink3` tabular; 1 px gridlines `K.line`; today marker 1 px `K.badLine` dashed 4/4 with a 6 px top triangle and label `Today` 10 px; at 6M, label every month; at 3M, every week faint + month strong; at All, every 2 months.
- Lane label column 120 px: 16 px icon + 12.5/500 label + count `(6)` 11 `K.ink3`. Lanes:
  | Lane | Icon | Colour | Events |
  |---|---|---|---|
  | Surgery | `content_cut`/`medical_services_outlined` | `K.accent` | craniotomy/biopsy, date, extent |
  | Radiotherapy | `radio_button_checked` / `bolt_outlined` | `K.teal` | RT start–end, dose/fractions |
  | Chemotherapy | `medication_outlined` | `K.chart3` | each TMZ cycle, planned cycles outlined |
  | Scans | `document_scanner_outlined` | `K.chart4` | MRI baseline, post-op, W6, W12 |
  | Visits | `event_outlined` | `K.ink2` | V0–V12, status |
- Bars: 12 px high, 3 px radius on the data end only; fill = lane colour at 12% opacity, 2 px solid lane colour border; label above/below if space, otherwise tooltip only. Planned = dashed 2 px `K.mutedLine`, 45% opacity, label `planned`. AI-only event = dashed `K.aiLine`, amber `AI · Unverified` pill in the rail; never amber for a verified event.
- Point events: 12 px circle, 2 px border, white fill; verified human-confirmed events fill the lane colour with a white check at ≥16 px? Keep the marker 12 px and put the check in the rail; do not shrink targets: each event has a 24×24 hit area minimum, 32 px for markers.
- Visits: small 8 px ticks on the bottom lane with V-code above; missed visit = red `K.badLine` diamond + `Missed`; scheduled = outline.
- Today marker and grid are non-interactive; `IgnorePointer`.
- Motion: when the tab opens, bars fade in once 180 ms; no per-bar stagger. Reduce-motion → instant.

### 4.4 Event interaction and evidence

- Every event is a real button (`InkWell`/`Semantics(button: true)`). Click selects: 2 px `K.accent` focus/selection ring around the bar or marker; the rail updates in 120 ms fade.
- Rail `TimelineEventPanel`:
  - Header: lane pill (`Surgery` `Tone.info`), date `01 Jun 2026` mono, event name `Craniotomy · gross total resection` `K.heading`.
  - Facts: key-value rows (`Extent` `Gross total`, `Surgeon` `SYN-AB`, `Source` `DOC-001-OP`), 12 labels `K.ink3`, values 14 `K.ink`.
  - State: `Verified` `Tone.ok` with actor/time; `AI · Unverified` amber with `Review` link; `Planned` muted; `Missed` bad.
  - Source: `EvidenceBox` with the exact excerpt (amber highlight) + `DOC-001-OP · p.1 ¶2 · 01 Jun 2026`; `Open source` primary 40 px opens the existing document dialog with the span in view; `Open in review` for AI events; `Raise query` if the event contradicts another record (monitor).
  - Footer: `Event #TL-004 · FHIR Procedure` mono 11 + `View audit` link.
- Rail below the selected event: `All events (14)` list, 40 px rows, grouped by month, keyboard `Up/Down`, `Enter` selects; this is the accessible fallback and the fast jump list. It scrolls independently.
- Clicking a visit row in `Overview` or an alert opens the timeline tab with the event selected and scrolled into view (`Scrollable.ensureVisible`, 200 ms, zero when reduced motion).

### 4.5 States

| State | Rendering |
|---|---|
| Empty | `EmptyState(Icons.timeline, 'No treatment events yet', 'Sync the FHIR connection or add a source document to build the timeline.')` + `Sync now` |
| No scans lane | If a lane has no events, hide the lane (not an empty row) and note `No scans recorded` in the legend tooltip |
| Loading | Axis + 3 skeleton lanes + rail skeleton; no full-page spinner; keep the participant header |
| Error | `ErrorState('Timeline unavailable. The local backend did not answer.', Retry)` inside the panel; keep the Overview link |
| Partial data | `2 events have no source document` amber note; those bars use a dashed outline and rail shows `No source`; they are not clickable to source but remain readable |
| Offline | Snapshot bars readable; `Open source` works from the cached document; `Raise query` disabled with offline tooltip |
| 200% text | Lane labels wrap to 2 lines; the rail stacks below the timeline; horizontal scroll allowed only inside the axis |

### 4.6 Widgets and acceptance

**Widgets:** `ParticipantTimelineScreen`, `SectionTabs`, `TimelineHeader`, `TimelineZoom`, `TimelineLanes` (`CustomPainter` axis/grid/today), `TimelineLane`, `TimelineEvent`, `TimelineMarker`, `TimelineLegend`, `EventRail`, `TimelineEventPanel`, `TimelineEventList`, `EvidenceBox`, `EvidenceLink`, `StatePill`, `EmptyState`, `Skeleton`.

**Acceptance**
- Surgery, RT (start/end with dose), each chemo cycle, scans and visits render on one axis with correct dates; planned vs done is visible without colour alone.
- Every event with a source opens the exact document excerpt; the selected state is visible in grayscale.
- Overview, dashboard alert and query deep links select the right event.
- 1440 and 1280 fit the 6M axis without horizontal scroll; <1024 falls back to the vertical list.
- Empty/loading/error/partial/offline states; 200% text and keyboard navigation pass.

---

## 5. Protocol → form builder

**Job:** the AI reads the protocol summary and proposes the form fields and eligibility criteria; the PI checks each proposal against the protocol text, excludes what is wrong, and approves a new version. Approval is the only way screening criteria change.

**Route:** `/protocol` (PLATFORM · Protocol → form). The screen is study-scoped; one protocol version at a time.

### 5.1 Layout (1440)

```
┌ PageHeader: Protocol → form      [Protocol v1.0 v] [Rules · local] [Analyse] ┐
│ GBM-NL-2026-01 · draft form v4 · 15 fields · 13 criteria · not approved    │
├──────────────────────┬──────────────────────────────┬──────────────────────┤
│ PROTOCOL 420         │ PROPOSALS                    │ APPROVAL 320         │
│ SYNTHETIC v1.0       │ [All | Fields | Criteria]    │ Active: form v3      │
│ Eligibility criteria │ ┌ FORM FIELDS (15) ────────┐ │ 15 fields · 13 crit. │
│ 1. Age ≥18 ...       │ │ ☑ Histology    coded     │ │ approved 18 Nov      │
│ 2. Histology ...     │ │   ICD-O-3 · MH.MHTERM    │ │ ───────────────────  │
│ [highlighted span]   │ │   [evidence] 0.96 AI     │ │ Draft: form v4       │
│                      │ └──────────────────────────┘ │ +2 fields +1 crit.   │
│                      │ ┌ INCLUSION (9) ───────────┐ │ [Approve & create]   │
│                      │ │ ☑ INC-01 Age ≥18          │ │ checklist            │
│                      │ │ ☑ INC-02 Histology ...    │ │ Version history      │
│                      │ └──────────────────────────┘ │ v3 · v2 · v1         │
└──────────────────────┴──────────────────────────────┴──────────────────────┘
```

- Page padding 24, panels fill height; each pane scrolls independently. No page scroll.
- At 1440: 420 / flex / 320, 16 gaps. At 1280: 360 / flex / 280; protocol text wraps. At <1200: protocol becomes a collapsible left drawer (`Protocol text` 44 px header) over the proposals; approval rail stays 280. At <900: proposals only, with `Protocol` and `Version` as tabs.
- Panels are `Panel(padding: EdgeInsets.zero)` with 44 px headers: `PROTOCOL · v1.0`, `PROPOSALS · draft v4`, `APPROVAL`.

### 5.2 Header and protocol pane

- PageHeader trailing: protocol version dropdown (240, `v1.0 (current)`, older read-only), provider chip `Rules · local` / `Ollama · local` 12 px (`K.mutedBg`, 1 px `K.mutedLine`), `Analyse protocol` `OutlinedButton.icon(Icons.auto_awesome)`.
- Subtitle: `GBM-NL-2026-01 · draft form v4 · 15 fields · 13 criteria · not approved`; after approval: `form v4 active since 23 Nov 2026`.
- Protocol pane header: document title, `v1.0 · 21 Nov 2026`, `SYNTHETIC` `Tone.ai` pill, overflow `Open document` / `Copy link`.
- Body: rendered synthetic synopsis, 14.5/26 max 62ch, `SelectableText.rich`. Section headings 15/500; paragraphs `K.body`.
- Evidence span: `#FFE1A8` with 2 px `K.aiLine` bottom rule, 3 px radius. Active span `#FFD08A` + 2 px `K.aiLine` underline. Never tint the whole paragraph.
- Clicking a proposal scrolls the protocol to its span; clicking a span selects the proposal. `EvidenceNavigator` 44 px at the bottom: `Evidence 1 of 2 · §5 ¶3` + prev/next + `Open document`.
- The pane is read-only. Editing the protocol is out of scope; a newer version triggers a stale-draft banner (5.5).

### 5.3 Proposal pane

- Header: `SegmentedButton` `All / Fields / Criteria` (32 px), search 200 px (`label or code`), sort `Protocol order` (fixed; no sort menu in the demo).
- Summary line above the list, 12.5: `15 fields · 9 inclusion · 4 exclusion · 2 excluded by you`; a 4 px stacked bar (included accent, excluded `K.line`, edited `K.aiLine`).
- Group headers 32 px `K.sidebar`: `FORM FIELDS (15)`, `INCLUSION (9)`, `EXCLUSION (4)`.
- `ProposalCard` (field) 12 radius, 12 padding, 8 gap, AI state:
  - Row 1: drag? no. 20 px include checkbox (checked by default; unchecked = excluded), label 14/500, right `Type` chip (`coded`, `date`, `integer`, `number`, `string`) neutral 11.
  - Row 2: mapping `CDISC DM.SEX` mono 11 `K.ink2` + `Required` toggle (16 px switch or checkbox) + `ICD-O-3` terminology chip.
  - Row 3: `EvidenceLink` (`§8 Table · row 3`) + confidence `0.96` mono + `AI · Unverified` `Tone.ai` pill (dashed).
  - Excluded: 55% opacity + `Excluded` muted pill; keep it in the list so the PI can undo.
  - Expanded (click card or chevron): evidence excerpt `EvidenceBox`, AI rationale `AI: protocol §8 lists HISTOLOGY as coded ICD-O-3; required in v1.0.` 12.5 `K.aiInk`, and `Edit` text (opens inline editor: label, type, required, mapping; 44 px fields) + `Reset` link. Edits change the card pill to `Edited` `Tone.info` and add to the approval diff. One audit event on approve, not per keystroke.
- `ProposalCard` (criterion) uses the same shell:
  - Code `INC-01` 52 px mono + text 14/500, right include checkbox.
  - Row 2: `Type` `Inclusion` / `Exclusion` chip, `Check` `eCRF AGE, MHSTDAT` 11.5 `K.ink2`, confidence.
  - Row 3: `EvidenceLink`, AI pill, `AI · Unverified`.
  - Expanded: protocol excerpt, `Data needed` line from `protocol_criteria.json`, and `Edit` for text/data-needed (never the code after approval).
- A 12 px note at the bottom: `AI proposals are not active. Screening uses the approved version only.`
- Sticky pane footer 56 px: `12 of 15 fields · 13 of 13 criteria selected` + `Approve & create version` primary (PI only; others disabled with tooltip).

### 5.4 Approval rail and versioning

- `Active version` card: `Form v3 · Active` `VersionPill(Tone.ok)`? Active is a human-approved version, so use `Tone.ok` with `check` for active; show `15 fields · 13 criteria`, `Approved by SYN-PI · 18 Nov 2026`, `View diff` text.
- `Draft version` card: `Form v4 · Draft` `Tone.ai`, counts `+2 fields`, `+1 criterion`, `1 changed`, `3 excluded`; badge `Not active`.
- Approval checklist 3 rows, 12.5:
  - `Every included field has evidence` (`check` green / `warning` amber).
  - `Every criterion is included or excluded` (`8 of 13 decided`).
  - `No duplicate field or criterion codes` (`check`).
  Blocked rows show the reason; the approve button tooltip repeats it.
- `Approve & create version` opens `ApproveVersionDialog` (520 px):
  1. Header `Approve form v4` + `Draft from protocol v1.0`.
  2. Diff summary 3-up tiles: `+2 fields`, `+1 criterion`, `1 changed`; a compact table of added/changed/removed (removed 0). Values are final labels, not IDs alone.
  3. Warning `Screening starts using v4 immediately. In-progress screenings keep their current version.` in `K.infoInk` on `K.infoBg`.
  4. Checkbox `I reviewed the fields and criteria against the protocol.` required.
  5. `Approve v4` primary + `Cancel` outline. Loading spinner in the button; 201/200 then close.
- Success: inline green panel at the top of the approval rail: `Form v4 approved · active 23 Nov 2026` `Tone.ok`, `View diff`, `Open screening`, `View audit event`. The draft card becomes `Active`; the old version moves to history; the approve button is disabled `v4 is active`. No acceptance modal after the dialog.
- `Version history` list: v3 (active until now), v2, v1; each 56 px row: version, date, approver, `15 fields · 13 criteria`, `View`. 24 px dot on the left, 1 px connector; current version `K.okLine`, superseded `K.mutedLine`. Keyboard accessible.
- PI only: analyse, edit proposals, approve. Nurse/designer read-only; monitor read-only. All see the version history and `View diff`.

### 5.5 States

| State | Rendering |
|---|---|
| No protocol | `EmptyState(Icons.description_outlined, 'No protocol loaded', 'Select a protocol version or upload a summary to propose fields and criteria.')`; proposals and approval disabled |
| No draft | `EmptyState(Icons.auto_awesome, 'No proposals yet', 'Analyse the protocol to propose fields and criteria.')` + `Analyse protocol` |
| Analysing | Protocol pane stays readable; proposals pane shows 5 skeleton cards and a 3 px accent progress bar under the header `Analysing protocol · 14 of 22 sections`; `Cancel` text; approve disabled |
| AI service down | Banner `AI service unavailable. The rules provider is still active.` + `Retry`; proposals from the last run remain visible but marked `Stale` |
| Stale draft | Banner `Protocol v1.1 is newer than this draft. Re-analyse or keep the draft.` with `Re-analyse` primary + `Keep draft` text; approval remains possible with an explicit checkbox? No: require re-analyse or PI acknowledgement; keep the demo simple: `Keep draft` is disabled until the PI checks `I reviewed the newer protocol` |
| Validation error | Inline list above the footer: `3 included fields have no evidence.` / `Duplicate code INC-03.`; approve disabled; error text names the item and has a `Show` link |
| Error (approve) | Dialog stays open with `Could not create version: <reason>. Nothing was changed.` in `K.badInk` above the actions; retry allowed |
| Offline | Read-only banner; Analyse/Edit/Approve disabled with `Reconnect the local backend to write.`; protocol and last proposals readable |
| 200% text | Panes stack internally; proposal cards grow; footer wraps to 2 rows but stays visible |

### 5.6 Widgets and acceptance

**Widgets:** `ProtocolFormBuilderScreen`, `ProtocolPane`, `ProtocolSpan`, `EvidenceNavigator`, `ProposalPane`, `ProposalFilterBar`, `ProposalGroupHeader`, `FieldProposalCard`, `CriterionProposalCard`, `ProposalEditor`, `ProposalFooter`, `ApprovalRail`, `VersionCard`, `ApprovalChecklist`, `VersionHistory`, `ApproveVersionDialog`, `DiffSummary`, `VersionPill`, `StatePill`, `EvidenceBox`, `EmptyState`, `Skeleton`.

**Acceptance**
- Analyse → proposals → exclude/edit → approve creates a new active form version and one audit event with the diff; screening uses only the new active version.
- Every proposal links to the protocol span; the active span is highlighted; keyboard selection works.
- Approve is impossible for non-PI, offline, with an undecided criterion, duplicate code, or missing evidence; the reason is visible.
- Diff counts and labels match the final proposals; removed items are shown, not hidden.
- Empty/analysing/error/stale/validation/offline states; 1440 and 1280 fit without page scroll; 200% text passes.

---

## 6. Implementation order and handover

1. **Shared (§0):** routes, nav, monitor banner + role gates, `v4_widgets.dart`, test keys. This unblocks all five.
2. **(1) Screening** and **(3) Queries** — released in commit d4ed06d; start here.
3. **(2) Site switcher** — dashboard only, reuse `MetricStrip`, `TableHead`, `DataRow2`, `Bar`.
4. **(4) Timeline** — participant tabs, `CustomPainter` axis, event rail, document dialog reuse.
5. **(5) Protocol → form** — highest risk; only after the API shape from D is stable. Keep it readable if the AI service is down.

**Non-goals for v4:** real signatures, e-signature timestamps, a second study, a mapping editor, protocol editing, query attachments beyond existing source documents, chart libraries, dark mode, animations beyond the D7b motion rules.

**Design artifacts:** `deliverables/design/v4/index.html` (five 1440×900 reference frames + states), `deliverables/design/v4/shots/` (PNG captures), `deliverables/design/v4/README.md` (how to view and capture). The HTML is a visual reference, not production code; the Markdown spec is the contract.

**Open items for D/F:**
- Exact query reply/close payloads and whether `answered` is a server state or derived; the UI needs one of the two.
- SDV endpoint currently exists as `POST /participants/{id}/ecrf/{field}/sdv`; confirm it returns actor/time and is idempotent.
- Screening sign-off needs a stable `criteriaVersion` on each decision so a later protocol version cannot rewrite history.
- Timeline event `source` must include `docId`, `page`, `span`, `excerpt`; without them the rail shows `No source`.
