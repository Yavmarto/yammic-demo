import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:yammic_demo/api/api.dart';
import 'package:yammic_demo/data/session.dart';
import 'package:yammic_demo/main.dart';
import 'package:flutter/material.dart';
import 'smoke_test.dart' as base;

/// v4 fake: the v3 fake plus the v4 endpoints. Records POSTs with bodies.
class V4Backend extends base.FakeBackend {
  final bodies = <String, Object?>{};
  var qStatus = 'open';
  Map q() => {'id': 7, 'participantId': 'GBM-NL-001', 'siteId': 'SITE-01', 'fieldId': 'KPS', 'status': qStatus, 'severity': 'high', 'text': 'KPS 90 vs 70 in letter?', 'openedBy': 'monitor', 'createdAt': '2026-11-20T09:00:00Z', 'closedBy': qStatus == 'closed' ? 'nurse' : null, 'closedAt': qStatus == 'closed' ? '2026-11-21T09:00:00Z' : null};

  @override
  Future<http.Response> handle(http.Request r) async {
    final p = r.url.path;
    Object? out;
    if (up && p == '/queries') {
      if (r.method == 'POST') {
        posts.add(p);
        bodies[p] = jsonDecode(r.body);
        out = q();
      } else {
        out = [q()];
      }
    } else if (up && p.startsWith('/queries/') && r.method == 'POST') {
      posts.add(p);
      qStatus = 'closed';
      out = q();
    }
    if (out == null) return super.handle(r);
    return http.Response.bytes(utf8.encode(jsonEncode(out)), 200, headers: {'content-type': 'application/json'});
  }
}

Future<(V4Backend, Session)> boot4(WidgetTester t, String role) async {
  t.view.physicalSize = const Size(1500, 1000);
  t.view.devicePixelRatio = 1;
  addTearDown(t.view.reset);
  final be = V4Backend();
  final s = Session(http: HttpApi(client: MockClient(be.handle)));
  await t.pumpWidget(DemoApp(session: s));
  await t.pump(const Duration(milliseconds: 300));
  await base.signIn(t, role);
  return (be, s);
}

void main() {
  testWidgets('queries: monitor asks, nurse resolves', (t) async {
    final (be, _) = await boot4(t, 'monitor');
    await t.tap(find.text('Queries').first);
    await base.settle(t);
    expect(find.text('KPS 90 vs 70 in letter?'), findsOneWidget);
    expect(find.byKey(const Key('close-7')), findsNothing);
    await t.tap(find.byKey(const Key('ask-query')));
    await t.pumpAndSettle();
    await t.enterText(find.byKey(const Key('q-participant')), 'GBM-NL-001');
    await t.enterText(find.byKey(const Key('q-text')), 'Confirm MGMT');
    await t.tap(find.byKey(const Key('q-send')));
    await base.settle(t);
    expect((be.bodies['/queries'] as Map)['text'], 'Confirm MGMT');
  });

  testWidgets('queries: nurse sees no ask button and resolves a query', (t) async {
    final (be, _) = await boot4(t, 'nurse');
    await t.tap(find.text('Queries').first);
    await base.settle(t);
    expect(find.byKey(const Key('ask-query')), findsNothing);
    await t.tap(find.byKey(const Key('q-7')));
    await t.pump(const Duration(milliseconds: 300));
    await t.tap(find.byKey(const Key('close-7')));
    await base.settle(t);
    expect(be.posts, contains('/queries/7/close'));
  });
}
