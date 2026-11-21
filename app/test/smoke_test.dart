import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:yammic_demo/api/api.dart';
import 'package:yammic_demo/data/session.dart';
import 'package:yammic_demo/main.dart';

const _text = 'KPS 90 at baseline. MGMT promoter is methylated.';
Map<String, dynamic> _ext(String id, String state, {double conf = .9}) => {
      'id': id, 'runId': 1, 'documentId': 'DOC-001-PATH', 'documentType': 'pathology_report', 'participantId': 'GBM-NL-001',
      'field': 'KPS', 'fieldLabel': 'Karnofsky score', 'status': 'proposed', 'value': '90', 'unit': null, 'confidence': conf,
      'proposedCode': null, 'abstentionReason': null, 'spanStart': 0, 'spanEnd': 6, 'evidence': [], 'provider': 'rules',
      'model': 'rules-regex-v1', 'promptVersion': 'rules_v1', 'reviewState': state, 'lastDecision': null,
    };

/// In-memory backend speaking the real wire format; records POSTs.
class FakeBackend {
  final posts = <String>[];
  var up = true;
  var state = 'pending';
  Future<http.Response> handle(http.Request r) async {
    if (!up) throw Exception('connection refused');
    final p = r.url.path;
    Object? body;
    if (r.method == 'POST') {
      posts.add(p);
      if (p == '/auth/login') {
        final u = jsonDecode(r.body)['username'];
        body = {'accessToken': 't', 'tokenType': 'bearer', 'user': {'username': u, 'role': u, 'name': 'Demo $u'}};
      } else if (p.endsWith('/decision')) {
        state = jsonDecode(r.body)['decision'] == 'accept' ? 'accepted' : 'deferred';
        body = {'extraction': {..._ext('EXT-1', state), 'lastDecision': {'decision': 'accept', 'username': 'nurse'}}, 'ecrfValue': null};
      }
    } else if (p == '/health') {
      body = {'status': 'ok', 'database': true};
    } else if (p.endsWith('/dashboard')) {
      body = {
        'studyId': 'GBM-NL-2026-01', 'title': 'Demo study', 'phase': 'II', 'status': 'recruiting',
        'kpis': {'enrolled': 8, 'target': 24, 'ecrfCompleteness': .5, 'ecrfFieldsTotal': 45, 'ecrfFieldsVerified': 22, 'openQueries': 9, 'sdvDone': 1, 'sdvPending': 2,
          'extractionsTotal': 2, 'extractionsPending': 2, 'extractionsReviewed': 0, 'extractionsAccepted': 0, 'extractionsCorrected': 0, 'extractionsRejected': 0, 'extractionsDeferred': 0, 'needsAttention': 1, 'aiAcceptanceRate': null},
        'sites': [{'id': 'SITE-01', 'name': 'Site one', 'shortName': 'Site one', 'city': 'Zuid', 'targetEnrolment': 10, 'enrolled': 3, 'openQueries': 4}],
        'milestones': [{'name': 'Interim review', 'date': '2026-12-15', 'done': false}],
        'alerts': [{'severity': 'warning', 'message': 'Check MGMT value'}],
        'tasks': [{'title': 'Review extractions', 'due': '2026-11-24', 'assignee': 'Nurse', 'participantId': 'GBM-NL-001'}],
      };
    } else if (p == '/participants') {
      body = [{'id': 'GBM-NL-001', 'studyId': 'S', 'siteId': 'SITE-01', 'status': 'active', 'statusDetail': 'on_treatment', 'age': 57, 'sex': 'F', 'enrolledDate': '2026-06-05', 'documentCount': 1, 'extractionsPending': 2, 'ecrfVerified': 0, 'ecrfTotal': 15, 'ecrfCompletePct': 0, 'openQueries': 1}];
    } else if (p.endsWith('/extractions')) {
      body = [_ext('EXT-1', state, conf: .5), _ext('EXT-2', 'pending')];
    } else if (p.startsWith('/documents/')) {
      body = {'id': 'DOC-001-PATH', 'text': _text, 'title': 'Path', 'sha256': 'abc', 'documentDate': '2026-06-05'};
    } else if (p == '/audit') {
      body = {'total': 1, 'items': [{'seq': 1, 'ts': '2026-11-21T10:00:00Z', 'actor': 'nurse', 'role': 'nurse', 'action': 'extraction.decision', 'entityType': 'extraction', 'entityId': 'EXT-1', 'participantId': null, 'before': null, 'after': {'x': 1}, 'source': 'human', 'model': null, 'promptVersion': null, 'prevHash': 'a' * 64, 'hash': 'b' * 64}]};
    } else if (p == '/audit/verify') {
      body = {'ok': true, 'count': 47, 'brokenSeq': null, 'reason': null, 'headHash': 'c' * 64};
    }
    return http.Response.bytes(utf8.encode(jsonEncode(body ?? {'detail': 'nope'})), body == null ? 404 : 200, headers: {'content-type': 'application/json'});
  }
}

Future<(FakeBackend, Session)> boot(WidgetTester t, {bool up = true}) async {
  t.view.physicalSize = const Size(1500, 1000);
  t.view.devicePixelRatio = 1;
  addTearDown(t.view.reset);
  final be = FakeBackend()..up = up;
  final s = Session(http: HttpApi(client: MockClient(be.handle)));
  await t.pumpWidget(DemoApp(session: s));
  await t.pump(const Duration(milliseconds: 300));
  return (be, s);
}

Future<void> signIn(WidgetTester t, String role) async {
  await t.tap(find.byKey(ValueKey('role-$role')));
  await t.pump();
  await t.tap(find.text('Use demo account'));
  await t.pump(const Duration(milliseconds: 100));
  await t.pump(const Duration(milliseconds: 600));
}

Future<void> settle(WidgetTester t) async {
  await t.runAsync(() => Future.delayed(const Duration(milliseconds: 150))); // real asset IO (offline snapshot)
  await t.pump(const Duration(milliseconds: 400));
  await t.pump(const Duration(milliseconds: 400));
}

void main() {
  testWidgets('login picks role, signs in via JWT and shows live dashboard KPIs', (t) async {
    final (be, s) = await boot(t);
    expect(find.text('Sign in'), findsWidgets);
    expect(find.textContaining('Synthetic data'), findsOneWidget);
    await signIn(t, 'pi');
    expect(be.posts, contains('/auth/login'));
    expect(s.role, 'pi');
    expect(find.text('Research dashboard'), findsOneWidget);
    expect(find.text('8/24'), findsOneWidget);
    expect(find.textContaining('Connected'), findsOneWidget);
    expect(find.textContaining('Synthetic data'), findsOneWidget);
  });

  testWidgets('review: Accept key posts a decision to the backend', (t) async {
    final (be, _) = await boot(t);
    await signIn(t, 'nurse');
    await t.tap(find.text('AI review').first);
    await settle(t);
    expect(find.text('AI extraction review'), findsOneWidget);
    await t.sendKeyEvent(LogicalKeyboardKey.keyA);
    await t.pump(const Duration(milliseconds: 300));
    expect(be.posts.any((p) => p.endsWith('/decision')), isTrue);
  });

  testWidgets('monitor role is read-only on review', (t) async {
    final (be, _) = await boot(t);
    await signIn(t, 'monitor');
    expect(find.text('Monitor role is read-only in this demo.'), findsWidgets);
    await t.tap(find.text('AI review').first);
    await settle(t);
    await t.sendKeyEvent(LogicalKeyboardKey.keyA);
    await t.pump(const Duration(milliseconds: 300));
    expect(be.posts.any((p) => p.endsWith('/decision')), isFalse);
  });

  testWidgets('audit: Verify chain shows the backend result', (t) async {
    await boot(t);
    await signIn(t, 'nurse');
    await t.tap(find.text('Audit trail').first);
    await settle(t);
    await t.tap(find.text('Verify chain'));
    await t.pump(const Duration(milliseconds: 300));
    expect(find.textContaining('Chain verified · 47 events'), findsOneWidget);
  });

  testWidgets('offline: backend down -> read-only snapshot, never crashes', (t) async {
    final (_, s) = await boot(t, up: false);
    expect(find.textContaining('Local backend is down'), findsWidgets);
    await signIn(t, 'nurse');
    await settle(t);
    expect(s.offline, isTrue);
    expect(find.text('Research dashboard'), findsOneWidget);
    expect(find.textContaining('Offline snapshot'), findsWidgets);
    expect(find.textContaining('Read-only until the local backend reconnects'), findsOneWidget);
    expect(find.textContaining('Synthetic data'), findsOneWidget);
    await t.tap(find.text('Participants').first);
    await settle(t);
    expect(find.text('GBM-NL-001'), findsWidgets);
  });
}
