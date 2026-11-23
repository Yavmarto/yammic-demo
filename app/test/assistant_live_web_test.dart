import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:yamicc_demo/api/api.dart';
import 'package:yamicc_demo/data/session.dart';
import 'package:yamicc_demo/features/assistant/assistant_screen.dart';

void main() {
  const token = String.fromEnvironment('ASSISTANT_TEST_TOKEN');
  testWidgets('live assistant question and action', (tester) async {
    final api = HttpApi(baseUrl: 'http://127.0.0.1:18753')..token = token;
    final session = Session(http: api);
    await tester.pumpWidget(
      SessionScope(
        session: session,
        child: const MaterialApp(home: Scaffold(body: AssistantScreen())),
      ),
    );
    await tester.enterText(find.byType(TextField), 'How do I review evidence?');
    await tester.runAsync(() async {
      await tester.tap(find.text('Send'));
      await Future<void>.delayed(const Duration(seconds: 1));
    });
    await tester.pumpAndSettle();
    expect(find.textContaining('Compare its quote'), findsOneWidget);
    await tester.runAsync(() async {
      await tester.tap(find.text('Enter a value manually'));
      await Future<void>.delayed(const Duration(seconds: 1));
    });
    await tester.pumpAndSettle();
    expect(find.textContaining('Enter from source'), findsOneWidget);
    await tester.enterText(find.byType(TextField), '!!!');
    await tester.runAsync(() async {
      await tester.tap(find.text('Send'));
      await Future<void>.delayed(const Duration(seconds: 1));
    });
    await tester.pumpAndSettle();
    expect(find.textContaining('could not complete'), findsOneWidget);
    await tester.enterText(find.byType(TextField), 'How do I export?');
    await tester.runAsync(() async {
      await tester.tap(find.text('Send'));
      await Future<void>.delayed(const Duration(seconds: 1));
    });
    await tester.pumpAndSettle();
    expect(find.textContaining('checked-data format'), findsOneWidget);
    await tester.runAsync(() async {
      try {
        await api.post('/assistant/action', {
          'version': 'v0.9.1',
          'action': {
            'name': 'unknown',
            'surfaceId': 'workflow-help-00000000000000000000000000000000',
            'sourceComponentId': 'choose-unknown',
            'timestamp': DateTime.now().toUtc().toIso8601String(),
            'context': {'kind': 'workflow_help'},
          },
        });
        fail('unknown action accepted');
      } on ApiException catch (e) {
        expect(e.status, 422);
      }
      try {
        await api.post('/assistant/action', {
          'version': 'v0.9.1',
          'action': {},
        });
        fail('malformed action accepted');
      } on ApiException catch (e) {
        expect(e.status, 422);
      }
    });
  }, skip: token.isEmpty);
}
