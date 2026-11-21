import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:yammic_demo/data/app_state.dart';
import 'package:yammic_demo/features/audit/audit_screen.dart';
import 'package:yammic_demo/features/review/review_screen.dart';
import 'package:yammic_demo/models/models.dart';
import 'package:yammic_demo/ui/widgets.dart';

Future<AppState> pump(WidgetTester t, Widget w) async {
  t.view.physicalSize = const Size(1440, 900);
  t.view.devicePixelRatio = 1;
  addTearDown(t.view.reset);
  final s = AppState();
  await t.pumpWidget(AppScope(state: s, child: MaterialApp(home: Scaffold(body: w))));
  for (var k = 0; k < 20 && find.byType(Skeleton).evaluate().isNotEmpty; k++) {
    await t.runAsync(() => Future.delayed(const Duration(milliseconds: 100)));
    await t.pump();
  }
  await t.pumpAndSettle();
  return s;
}

List<AuditEvent> human(AppState s) => s.audit.events.where((e) => e.source == EventSource.human).toList();

void main() {
  testWidgets('accept writes a human audit event', (t) async {
    final s = await pump(t, const ReviewScreen(participantId: 'GBM-NL-001'));
    await t.tap(find.text('Accept'));
    await t.pumpAndSettle();
    expect(human(s).single.action, 'accept');
    expect(human(s).single.after, isNotNull);
    expect(find.text('Verified · Accepted'), findsWidgets);
  });

  testWidgets('keyboard A accepts, X opens reject dialog and rejects with reason', (t) async {
    final s = await pump(t, const ReviewScreen(participantId: 'GBM-NL-001'));
    await t.sendKeyEvent(LogicalKeyboardKey.keyA);
    await t.pumpAndSettle();
    expect(human(s).single.action, 'accept');
    await t.sendKeyEvent(LogicalKeyboardKey.keyX);
    await t.pumpAndSettle();
    await t.tap(find.text('Not in source'));
    await t.pump();
    await t.tap(find.widgetWithText(FilledButton, 'Reject'));
    await t.pumpAndSettle();
    expect(human(s).last.action, 'reject');
    expect(human(s).last.after, 'rejected: Not in source');
  });

  testWidgets('correct logs before and after; audit screen lists it', (t) async {
    final s = await pump(t, const ReviewScreen(participantId: 'GBM-NL-001'));
    await t.tap(find.text('Correct'));
    await t.pumpAndSettle();
    await t.enterText(find.byType(TextField), 'edited');
    await t.tap(find.text('Save correction'));
    await t.pumpAndSettle();
    final e = human(s).single;
    expect([e.action, e.after], ['correct', 'edited']);
    expect(e.before, isNotNull);

    await t.pumpWidget(AppScope(state: s, child: const MaterialApp(home: Scaffold(body: AuditScreen()))));
    await t.pumpAndSettle();
    expect(find.descendant(of: find.byKey(const ValueKey('audit-row-0')), matching: find.text('correct')), findsOneWidget);
  });
}
