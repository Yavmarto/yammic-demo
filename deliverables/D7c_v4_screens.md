# D7c — v4 screens: five new features in the v3 visual language

**Owner:** Designer · **For:** Engineer (F), CTO (D), PM, QA · **Date:** 2026-11-21
**Status:** implementation spec on branch `v4` · **Due:** Sun 2026-11-22 09:00 CET
**Read first:** `deliverables/D7b_visual_direction.md` (the visual contract), `app/lib/theme/tokens.dart` (live tokens), `deliverables/design/w7_after/` (v3 screenshots).
**Reference frames:** `deliverables/design/v4/index.html` and `shots/` (same tokens, same shell).
**Source data:** `deliverables/protocol_GBM-NL-2026-01_synopsis.md`, `deliverables/protocol_criteria.json`.

This document adds **only** what is new. Everything in D7b still applies: Panel not Card, borders not shadows, IBM Plex Sans 300/400/500, accent `#0073E6`, the AI/verified/integrity colour grammar, 4/8/12/16/24/32/48 spacing, 40 px targets, 12.5 px small text, tabular numbers, no dark mode, no page-load choreography, synthetic banner on every screen.

Sections 1 and 3 are released first so the Engineer can start. Sections 2, 4 and 5 follow in the same file before 09:00.

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

<!-- Sections 2, 4, 5 are appended below before 09:00. -->
