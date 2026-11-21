# Demo tech spec (CEL-1752)

Target: stable MVP demo Monday 2026-11-23. Code freeze Sun 2026-11-22 20:00 CET. Synthetic data only. No network, backend or live AI calls. Banner "Synthetic data — prototype, not for clinical use" on every screen (rendered by the shell).

## Stack
Flutter 3.47.5 (`~/flutter/bin/flutter`), Dart ^3.13, Material 3 with the Zeta design system (`zeta_flutter 1.4.5`, exact pin; `ZetaProvider` theme, Zeta navigation rail and semantic colours). Targets: web + macOS. Only runtime package beyond the Flutter SDK: `zeta_flutter` (dev: `flutter_lints 6.0.0`). State: one `AppState` (ChangeNotifier) in an `AppScope` InheritedWidget; audit log is its own ChangeNotifier. Routing: `MaterialApp.onGenerateRoute` with named routes.

## Layout (`app/lib`)
- `main.dart`, `shell/` — app, routes, nav rail, banner (CTO)
- `models/models.dart` — all Dart models = JSON schema (CTO)
- `data/` — `app_state.dart` (JSON loader), `audit_store.dart` (CTO)
- `features/dashboard/` UI-001, `features/participant/` UI-002 (CTO)
- `features/review/`, `features/audit/` (Engineer; stubs exist: `ReviewScreen`, `AuditScreen`)
- `assets/data/` — `dashboard.json`, `participants.json`, `extractions.json` (Junior Engineer; must match models.dart)

## Routes
`/` dashboard · `/participants` list · `/participant/<id>` workspace · `/review` (optional arg: participant id) · `/audit`

## Data model
See `app/lib/models/models.dart`; field comments list allowed enum strings. Top level:
- `dashboard.json`: `{studies, sites, milestones, alerts, tasks}`
- `participants.json`: `{participants:[{id,studyId,siteId,status,age,sex,summary,visits,ecrfs,issues,treatments}]}`
- `extractions.json`: `{extractions:[{id,participantId,field,value,sourceText,spanStart,spanEnd,confidence,model,promptVersion}]}`
Dates are ISO `yyyy-MM-dd`. Participant ids look like `SYN-0001`.

## Audit store
`AppScope.of(context).audit.record(actor, action, field, before, after, source: EventSource.ai|human, model, promptVersion)`. Append-only (no edit/delete), timestamp set on write. Read `audit.events`; listen with `ListenableBuilder(listenable: audit, ...)`.

## Ownership
CTO: main/shell/routing/models/data/dashboard/participant. Engineer: review + audit features only (do not edit models.dart; ask CTO). Junior Engineer: `assets/data/*.json`.

## Commands (run in `app/`)
```
F=~/flutter/bin/flutter
$F pub get
$F analyze
$F run -d chrome        # or -d macos
$F build web --release
$F build macos
```
