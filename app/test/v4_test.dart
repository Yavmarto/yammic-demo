import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:yamicc_demo/api/api.dart';
import 'package:yamicc_demo/data/session.dart';
import 'package:yamicc_demo/main.dart';
import 'package:flutter/material.dart';
import 'smoke_test.dart' as base;

/// v4 fake: the v3 fake plus the v4 endpoints. Records POSTs with bodies.
class V4Backend extends base.FakeBackend {
  final bodies = <String, Object?>{};
  var qStatus = 'open';
  var scrStatus = 'screening';
  var formStatus = 'proposed';
  final confirmed = <String>{};
  Map fv(int v, String st) => {'id': v, 'studyId': 'GBM-NL-2026-01', 'formId': 'ECRF-GBM-BASELINE', 'version': v, 'status': st, 'proposedBy': 'rules', 'proposedAt': '2026-11-21T10:00:00Z', 'provider': 'rules', 'model': 'm',
        'fields': [{'id': 'KPS', 'label': 'Karnofsky', 'section': 'clinical', 'valueType': 'integer', 'required': true, 'sourceSentence': 'KPS at least 60.'}],
        'criteria': [{'id': 'INC-04', 'type': 'inclusion', 'text': 'KPS 60 or higher'}]};
  Map crit(String id, String ai, String type) => {'id': 'GBM-NL-009:$id', 'criterionId': id, 'ord': 1, 'type': type, 'text': 'Criterion $id', 'aiStatus': ai, 'confidence': .9, 'coordinatorStatus': confirmed.contains(id) ? ai : null, 'effectiveStatus': ai,
        'documentId': ai == 'met' ? 'DOC-001-PATH' : null, 'evidence': ai == 'met' ? [{'start': 0, 'end': 6, 'text': 'KPS 90'}] : [], 'rationale': 'KPS 90 recorded', 'provider': 'rules'};
  Map scr() => {'participantId': 'GBM-NL-009', 'studyId': 'GBM-NL-2026-01', 'siteId': 'SITE-02', 'status': scrStatus, 'metCount': 2, 'notMetCount': 0, 'unknownCount': 0, 'confirmedCount': confirmed.length, 'totalCount': 2,
        'coordinatorSignedBy': scrStatus == 'screening' ? null : 'nurse', 'coordinatorSignedAt': scrStatus == 'screening' ? null : '2026-11-21T14:12:00Z',
        'criteria': [crit('INC-01', 'met', 'inclusion'), crit('EXC-01', 'met', 'exclusion')]};
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
      bodies[p] = r.body.isEmpty ? null : jsonDecode(r.body);
      qStatus = p.endsWith('/answer') ? 'answered' : 'closed';
      out = q();
    } else if (up && p == '/screening') {
      out = [scr()];
    } else if (up && p.startsWith('/participants/GBM-NL-009/screening/') && r.method == 'POST') {
      posts.add(p);
      bodies[p] = r.body.isEmpty ? null : jsonDecode(r.body);
      if (p.endsWith('/confirm')) {
        confirmed.add(p.split('/')[5]);
      } else if (p.endsWith('/sign-off')) {
        scrStatus = (bodies[p] as Map)['decision'] as String;
      }
      out = scr();
    } else if (up && p == '/participants/GBM-NL-001/timeline') {
      out = {'participantId': 'GBM-NL-001', 'events': [
        {'id': 'e2', 'category': 'surgery', 'title': 'Craniotomy', 'date': '2026-05-10', 'status': 'completed', 'detail': 'Gross total', 'documentId': 'DOC-001-PATH', 'documentTitle': 'Path'},
        {'id': 'e1', 'category': 'scan', 'title': 'MRI baseline', 'date': '2026-05-01'},
      ]};
    } else if (up && p == '/studies/GBM-NL-2026-01/forms') {
      out = [fv(2, formStatus), fv(1, 'approved')];
    } else if (up && p.startsWith('/studies/GBM-NL-2026-01/forms/')) {
      posts.add(p);
      bodies[p] = r.body.isEmpty ? null : jsonDecode(r.body);
      formStatus = p.endsWith('/approve') ? 'approved' : 'proposed';
      out = fv(2, formStatus);
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

  testWidgets('queries: nurse sees no ask button and answers a query', (t) async {
    final (be, _) = await boot4(t, 'nurse');
    await t.tap(find.text('Queries').first);
    await base.settle(t);
    expect(find.byKey(const Key('ask-query')), findsNothing);
    await t.tap(find.byKey(const Key('q-7')));
    await t.pump(const Duration(milliseconds: 300));
    expect(find.byKey(const Key('close-7')), findsNothing);
    await t.enterText(find.byKey(const Key('answer-text')), 'KPS 90 is correct');
    await t.tap(find.byKey(const Key('answer-7')));
    await base.settle(t);
    expect((be.bodies['/queries/7/answer'] as Map)['answer'], 'KPS 90 is correct');
  });

  testWidgets('screening: confirm every criterion, then sign off', (t) async {
    final (be, _) = await boot4(t, 'nurse');
    await t.tap(find.text('Screening').first);
    await base.settle(t);
    expect(find.text('GBM-NL-009'), findsWidgets);
    expect(find.text('AI proposals only · 0 human-confirmed'), findsOneWidget);
    expect(t.widget<FilledButton>(find.byKey(const Key('signoff'))).onPressed, isNull);
    for (final id in ['INC-01', 'EXC-01']) {
      await t.tap(find.byKey(Key('crit-$id')));
      await t.pump(const Duration(milliseconds: 300));
      await t.tap(find.byKey(Key('met-$id')));
      await base.settle(t);
    }
    expect(find.text('2 of 2 confirmed by a person'), findsOneWidget);
    await t.tap(find.byKey(const Key('signoff')));
    await t.pumpAndSettle();
    await t.tap(find.byKey(const Key('checked-all')));
    await t.pump();
    await t.tap(find.byKey(const Key('signoff-submit')));
    await base.settle(t);
    expect((be.bodies['/participants/GBM-NL-009/screening/sign-off'] as Map)['decision'], 'eligible');
    expect(find.byKey(const Key('signed-banner')), findsOneWidget);
  });

  testWidgets('screening: monitor cannot sign off', (t) async {
    await boot4(t, 'monitor');
    await t.tap(find.text('Screening').first);
    await base.settle(t);
    expect(t.widget<FilledButton>(find.byKey(const Key('signoff'))).onPressed, isNull);
  });

  testWidgets('timeline: events in date order, filter, source link opens document', (t) async {
    await boot4(t, 'nurse');
    await t.tap(find.text('Participants').first);
    await base.settle(t);
    t.state<NavigatorState>(find.byType(Navigator)).pushNamed('/participants/GBM-NL-001/timeline');
    await base.settle(t);
    expect(t.getTopLeft(find.text('MRI baseline')).dy < t.getTopLeft(find.text('Craniotomy')).dy, isTrue);
    await t.tap(find.byKey(const Key('doc-e2')));
    await base.settle(t);
    expect(find.textContaining('KPS 90 at baseline'), findsOneWidget);
  });

  testWidgets('protocol: nurse analyses, only PI approves', (t) async {
    final (be, _) = await boot4(t, 'nurse');
    await t.tap(find.text('Protocol → form').first);
    await base.settle(t);
    expect(find.text('Draft · AI proposal'), findsWidgets);
    expect(t.widget<FilledButton>(find.byKey(const Key('approve'))).onPressed, isNull);
    await t.tap(find.byKey(const Key('analyse')));
    await base.settle(t);
    expect(be.posts, contains('/studies/GBM-NL-2026-01/forms/propose'));
  });

  testWidgets('protocol: PI approves a version', (t) async {
    final (be, _) = await boot4(t, 'pi');
    await t.tap(find.text('Protocol → form').first);
    await base.settle(t);
    await t.tap(find.byKey(const Key('approve')));
    await t.pumpAndSettle();
    await t.tap(find.byKey(const Key('approve-confirm')));
    await base.settle(t);
    expect(be.posts, contains('/studies/GBM-NL-2026-01/forms/2/approve'));
  });
}
