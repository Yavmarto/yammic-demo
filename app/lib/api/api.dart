import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

/// Backend answered with an error status.
class ApiException implements Exception {
  final int status;
  final String message;
  ApiException(this.status, this.message);
  @override
  String toString() => message;
}

/// Backend could not be reached (or the offline snapshot lacks the data).
class Unreachable implements Exception {
  final String message;
  Unreachable([this.message = 'Backend unreachable']);
  @override
  String toString() => message;
}

/// One seam for the FastAPI backend (backend/openapi.json). JSON in, JSON out;
/// screens read the decoded camelCase maps directly. Fake it in tests.
abstract class Api {
  Future<dynamic> get(String path, {Map<String, String>? query});
  Future<dynamic> post(String path, [Object? body]);
}

const defaultBaseUrl = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://127.0.0.1:8003');

class HttpApi implements Api {
  final String baseUrl;
  final http.Client _c;
  String? token;
  HttpApi({this.baseUrl = defaultBaseUrl, http.Client? client}) : _c = client ?? http.Client();

  Map<String, String> get _h => {
        'content-type': 'application/json',
        if (token != null) 'authorization': 'Bearer $token',
      };

  Future<dynamic> _send(Future<http.Response> Function() f) async {
    final http.Response r;
    try {
      r = await f().timeout(const Duration(seconds: 6));
    } catch (_) {
      throw Unreachable('Cannot reach the local backend at $baseUrl');
    }
    Object? body;
    try {
      body = r.body.isEmpty ? null : jsonDecode(utf8.decode(r.bodyBytes));
    } on FormatException {
      if (r.statusCode < 400) throw ApiException(r.statusCode, 'Unexpected response from the backend');
    }
    if (r.statusCode >= 400) {
      final d = body is Map ? body['detail'] : null;
      throw ApiException(r.statusCode, d is String ? d : r.statusCode >= 500 ? 'The backend failed to process the request (${r.statusCode}). Try again.' : 'Request failed (${r.statusCode})');
    }
    return body;
  }

  @override
  Future<dynamic> get(String path, {Map<String, String>? query}) =>
      _send(() => _c.get(Uri.parse('$baseUrl$path').replace(queryParameters: query), headers: _h));

  @override
  Future<dynamic> post(String path, [Object? body]) =>
      _send(() => _c.post(Uri.parse('$baseUrl$path'), headers: _h, body: jsonEncode(body ?? {})));

  /// GET a non-JSON body (ODM XML, FHIR bundle text).
  Future<String> getText(String path) async {
    final http.Response r;
    try {
      r = await _c.get(Uri.parse('$baseUrl$path'), headers: _h).timeout(const Duration(seconds: 20));
    } catch (_) {
      throw Unreachable('Cannot reach the local backend at $baseUrl');
    }
    if (r.statusCode >= 400) {
      final b = jsonDecode(utf8.decode(r.bodyBytes));
      throw ApiException(r.statusCode, b is Map && b['detail'] is String ? b['detail'] : 'Request failed (${r.statusCode})');
    }
    return utf8.decode(r.bodyBytes);
  }
}

/// Read-only snapshot served from bundled synthetic JSON when the backend is down.
class OfflineApi implements Api {
  final AssetBundle? bundle;
  OfflineApi([this.bundle]);
  final _cache = <String, dynamic>{};

  Future<dynamic> _json(String f) async => _cache[f] ??= jsonDecode(await (bundle ?? rootBundle).loadString('assets/data/$f'));

  @override
  Future<dynamic> post(String path, [Object? body]) => throw Unreachable('Offline snapshot is read-only');

  @override
  Future<dynamic> get(String path, {Map<String, String>? query}) async {
    final p = path.split('/').where((s) => s.isNotEmpty).toList();
    if (p.length == 3 && p[0] == 'studies') return _dashboard();
    if (p.isNotEmpty && p[0] == 'participants') {
      final parts = (await _json('participants.json'))['participants'] as List;
      final ex = (await _json('extractions.json'))['extractions'] as List;
      int pend(Object? id) => ex.where((e) => e['participantId'] == id).length;
      if (p.length == 1) return [for (final x in parts) {..._summary(x), 'extractionsPending': pend(x['id'])}];
      final one = parts.cast<Map>().firstWhere((x) => x['id'] == p[1], orElse: () => throw ApiException(404, 'Participant not found'));
      if (p.length == 2) return {..._summary(one), 'extractionsPending': pend(one['id']), ...one};
      if (p[2] == 'extractions') return _extractions(p[1]);
      if (p[2] == 'documents') return _documents(p[1]);
      if (p[2] == 'ecrf') return {'participantId': p[1], 'formId': 'ECRF-GBM-BASELINE', 'verified': 0, 'total': 0, 'completePct': 0, 'fields': []};
    }
    if (p.length == 2 && p[0] == 'documents') {
      final d = (await _documents(null)).firstWhere((x) => x['id'] == p[1]);
      return {...d, 'text': await (bundle ?? rootBundle).loadString('assets/data/documents/${p[1]}.txt')};
    }
    if (p.isNotEmpty && p[0] == 'audit') {
      if (p.length == 2) return {'ok': false, 'count': 0, 'brokenSeq': null, 'reason': 'Not available offline'};
      return {'total': 0, 'items': []};
    }
    throw Unreachable('Not part of the offline snapshot');
  }

  Map<String, dynamic> _summary(Map x) => {
        'id': x['id'], 'studyId': x['studyId'], 'siteId': x['siteId'], 'status': x['status'], 'statusDetail': x['statusDetail'],
        'age': x['age'], 'sex': x['sex'], 'enrolledDate': x['enrolledDate'],
        'documentCount': (x['documentIds'] as List).length, 'extractionsPending': 0, 'ecrfVerified': 0, 'ecrfTotal': 0,
        'ecrfCompletePct': ((x['ecrfs'] as List?)?.isNotEmpty ?? false) ? (x['ecrfs'] as List).first['completePct'] : 0, 'openQueries': (x['issues'] as List?)?.length ?? 0,
      };

  Future<List<Map<String, dynamic>>> _documents(String? pid) async =>
      [for (final d in (await _json('documents.json'))['documents'] as List) if (pid == null || d['participantId'] == pid) Map<String, dynamic>.from(d)];

  Future<List<dynamic>> _extractions(String pid) async => [
        for (final e in (await _json('extractions.json'))['extractions'] as List)
          if (e['participantId'] == pid)
            {...Map<String, dynamic>.from(e), 'provider': 'fixture', 'reviewState': 'pending', 'lastDecision': null}..remove('sourceText'),
      ];

  Future<Map<String, dynamic>> _dashboard() async {
    final d = await _json('dashboard.json');
    final s = (d['studies'] as List).first;
    final ex = (await _json('extractions.json'))['extractions'] as List;
    return {
      'studyId': s['id'], 'title': s['title'], 'phase': s['phase'], 'status': 'recruiting', 'synthetic': true, 'disclaimer': d['disclaimer'],
      'kpis': {
        'enrolled': s['enrolled'], 'target': s['target'], 'ecrfCompleteness': s['completeness'], 'extractionsTotal': ex.length,
        'extractionsPending': ex.length, 'extractionsReviewed': 0, 'extractionsAccepted': 0, 'extractionsCorrected': 0, 'extractionsRejected': 0,
        'extractionsDeferred': 0, 'ecrfFieldsTotal': 0, 'ecrfFieldsVerified': 0, 'needsAttention': ex.where((e) => e['status'] == 'abstained' || (e['confidence'] as num) < .6).length,
        'openQueries': (d['sites'] as List).fold<int>(0, (a, x) => a + (x['openQueries'] as int)), 'auditEvents': 0, 'sdvDone': 0, 'sdvPending': 0,
      },
      'sites': [for (final x in d['sites'] as List) {'id': x['id'], 'name': x['name'], 'shortName': x['name'], 'city': null, 'targetEnrolment': x['target'], 'enrolled': x['enrolled'], 'openQueries': x['openQueries']}],
      'milestones': d['milestones'], 'alerts': d['alerts'], 'tasks': d['tasks'],
    };
  }
}
