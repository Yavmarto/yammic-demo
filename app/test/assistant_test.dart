import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:yamicc_demo/api/api.dart';
import 'package:yamicc_demo/data/session.dart';
import 'package:yamicc_demo/features/assistant/assistant_screen.dart';

Map<String, dynamic> surface(String answer) => {
  'messages': [
    {
      'version': 'v0.9.1',
      'createSurface': {
        'surfaceId': 'workflow-help-abc',
        'catalogId':
            'https://a2ui.org/specification/v0_9_1/catalogs/basic/catalog.json',
      },
    },
    {
      'version': 'v0.9.1',
      'updateComponents': {
        'surfaceId': 'workflow-help-abc',
        'components': [
          {
            'id': 'root',
            'component': 'Column',
            'children': ['answer', 'choose-manual'],
          },
          {'id': 'answer', 'component': 'Text', 'text': answer},
          {
            'id': 'label',
            'component': 'Text',
            'text': 'Enter a value manually',
          },
          {
            'id': 'choose-manual',
            'component': 'Button',
            'child': 'label',
            'action': {
              'event': {
                'name': 'manual',
                'context': {'kind': 'workflow_help'},
              },
            },
          },
        ],
      },
    },
  ],
};

void main() {
  testWidgets('choice, retry, and malformed response', (tester) async {
    var attempts = 0;
    Map? action;
    final client = MockClient((request) async {
      if (request.url.path == '/assistant/action') {
        action = jsonDecode(request.body) as Map;
        if (++attempts == 1) return http.Response('{}', 503);
        return http.Response(jsonEncode(surface('Enter from source')), 200);
      }
      if (jsonDecode(request.body)['text'] == 'bad') {
        return http.Response('{"messages":[]}', 200);
      }
      return http.Response(jsonEncode(surface('Compare its quote')), 200);
    });
    final session = Session(http: HttpApi(client: client));
    await tester.pumpWidget(
      SessionScope(
        session: session,
        child: const MaterialApp(home: Scaffold(body: AssistantScreen())),
      ),
    );
    await tester.enterText(find.byType(TextField), 'How do I review evidence?');
    await tester.tap(find.text('Send'));
    await tester.pumpAndSettle();
    expect(find.text('Compare its quote'), findsOneWidget);
    await tester.tap(find.text('Enter a value manually'));
    await tester.pumpAndSettle();
    expect(find.text('Try again'), findsOneWidget);
    expect(action!['version'], 'v0.9.1');
    expect(action!['action']['sourceComponentId'], 'choose-manual');
    expect(DateTime.tryParse(action!['action']['timestamp']), isNotNull);
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(find.text('Enter from source'), findsOneWidget);
    await tester.enterText(find.byType(TextField), 'bad');
    await tester.tap(find.text('Send'));
    await tester.pumpAndSettle();
    expect(find.textContaining('invalid response'), findsOneWidget);
  });
}
