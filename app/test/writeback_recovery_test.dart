import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:yamicc_demo/api/api.dart';
import 'package:yamicc_demo/data/session.dart';
import 'package:yamicc_demo/features/export/export_screen.dart';

void main() {
  testWidgets('stale review must be refreshed; transient failure retains identity', (tester) async {
    tester.view.physicalSize = const Size(1500, 1200);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    var version = 1;
    var status = 409;
    final sent = <String>[];
    final api = HttpApi(client: MockClient((request) async {
      if (request.url.path == '/participants') return http.Response('[]', 200);
      if (request.method == 'GET') {
        return http.Response(jsonEncode({'deliveryId': 'id-$version', 'destination_field': 'KPS', 'review_state': 'corrected', 'value': version == 1 ? 80 : 90, 'source_id': 'DOC-1', 'extraction_id': 'EX-1'}), 200);
      }
      sent.add((jsonDecode(request.body) as Map)['deliveryId'] as String);
      if (status == 0) throw Exception('connection lost');
      return http.Response(jsonEncode({'detail': 'failure'}), status);
    }));
    final session = Session(http: api)..user = {'role': 'pi'};
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SessionScope(session: session, child: const ExportScreen()))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Review synthetic delivery'));
    await tester.pumpAndSettle();
    expect(find.textContaining('value: 80'), findsOneWidget);
    await tester.tap(find.text('Send reviewed value'));
    await tester.pumpAndSettle();
    expect(find.textContaining('no longer current'), findsOneWidget);
    expect(find.textContaining('value: 80'), findsNothing);
    expect(find.text('Retry delivery'), findsNothing);
    version = 2;
    status = 503;
    await tester.tap(find.text('Review synthetic delivery'));
    await tester.pumpAndSettle();
    expect(find.textContaining('value: 90'), findsOneWidget);
    await tester.tap(find.text('Send reviewed value'));
    await tester.pumpAndSettle();
    expect(find.text('Retry delivery'), findsOneWidget);
    await tester.tap(find.text('Retry delivery'));
    await tester.pumpAndSettle();
    status = 0;
    await tester.tap(find.text('Retry delivery'));
    await tester.pumpAndSettle();
    expect(find.text('Retry delivery'), findsOneWidget);
    await tester.tap(find.text('Retry delivery'));
    await tester.pumpAndSettle();
    expect(sent, ['id-1', 'id-2', 'id-2', 'id-2', 'id-2']);
  });
}
