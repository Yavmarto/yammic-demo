import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:yamicc_demo/api/api.dart';
import 'package:yamicc_demo/data/session.dart';
import 'package:yamicc_demo/features/review/review_screen.dart';

void main() {
  for (final role in ['nurse', 'monitor']) {
    testWidgets('failed run feedback for $role', (t) async {
      t.view.physicalSize = const Size(1600, 1100);
      t.view.devicePixelRatio = 1;
      addTearDown(t.view.reset);
      var posts = 0;
      final httpApi = HttpApi(client: MockClient((request) async {
        Object body = [];
        if (request.url.path == '/runs' && request.method == 'GET') {
          body = [{'id': 42, 'participantId': 'P1', 'status': 'failed', 'error': 'secret provider text'}];
        } else if (request.url.path == '/runs/42/retry') {
          posts++;
          body = {'id': 43, 'participantId': 'P1', 'status': 'queued', 'done': 0, 'total': 0};
        } else if (request.url.path == '/runs/43') {
          body = {'id': 43, 'participantId': 'P1', 'status': 'completed', 'done': 1, 'total': 1};
        }
        return http.Response(jsonEncode(body), 200, headers: {'content-type': 'application/json'});
      }));
      final session = Session(http: httpApi)..user = {'username': role, 'role': role};
      await t.pumpWidget(MaterialApp(home: SessionScope(session: session, child: const Scaffold(body: ReviewScreen(participantId: 'P1')))));
      await t.pump();
      await t.pump(const Duration(milliseconds: 300));
      expect(find.text('Extraction failed. The provider could not complete this run.'), findsOneWidget);
      expect(find.textContaining('secret provider text'), findsNothing);
      if (role == 'monitor') {
        expect(find.text('Retry extraction'), findsNothing);
      } else {
        await t.tap(find.text('Retry extraction'));
        await t.pump();
        expect(posts, 1);
        expect(find.text('Retry queued.'), findsOneWidget);
        await t.pump(const Duration(milliseconds: 800));
        await t.pump();
        expect(find.textContaining('Extraction complete'), findsOneWidget);
      }
    });
  }
}
