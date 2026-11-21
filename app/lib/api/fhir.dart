import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api.dart';

const defaultFhirBase = String.fromEnvironment('FHIR_BASE_URL', defaultValue: 'http://localhost:8090/fhir');

/// Minimal read/push client for the local HAPI FHIR R4 server.
class FhirClient {
  final String base;
  final http.Client _c;
  FhirClient({this.base = defaultFhirBase, http.Client? client}) : _c = client ?? http.Client();

  Future<Map> _json(Future<http.Response> Function() f) async {
    final http.Response r;
    try {
      r = await f().timeout(const Duration(seconds: 8));
    } catch (_) {
      throw Unreachable('Cannot reach FHIR server at $base');
    }
    final body = jsonDecode(utf8.decode(r.bodyBytes));
    if (r.statusCode >= 400) throw ApiException(r.statusCode, 'FHIR server answered ${r.statusCode}');
    return body as Map;
  }

  Future<Map> metadata() => _json(() => _c.get(Uri.parse('$base/metadata')));

  Future<int> count(String type) async => ((await _json(() => _c.get(Uri.parse('$base/$type?_summary=count'))))['total'] as num?)?.toInt() ?? 0;

  /// POST a transaction bundle; returns the response bundle.
  Future<Map> push(Map bundle) =>
      _json(() => _c.post(Uri.parse(base), headers: {'content-type': 'application/fhir+json'}, body: jsonEncode(bundle)));
}
