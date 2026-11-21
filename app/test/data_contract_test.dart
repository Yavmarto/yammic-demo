// Contract test: the synthetic fixtures must parse through the Dart models in
// lib/models/models.dart. Spans are validated independently by
// tool/validate_data.py; this test guards the app-facing JSON shape.

import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:yammic_demo/models/models.dart';

Map<String, dynamic> _read(String path) =>
    jsonDecode(File(path).readAsStringSync()) as Map<String, dynamic>;

void main() {
  test('dashboard.json parses into Dashboard', () {
    final d = Dashboard.fromJson(_read('assets/data/dashboard.json'));
    expect(d.studies, isNotEmpty);
    expect(d.sites.length, 3);
  });

  test('participants.json parses into Participant list', () {
    final raw = _read('assets/data/participants.json');
    final list = (raw['participants'] as List)
        .map((e) => Participant.fromJson(e as Map<String, dynamic>))
        .toList();
    expect(list.length, inInclusiveRange(6, 10));
    expect(list.every((p) => p.id.startsWith('GBM-NL-')), isTrue);
    expect(list.every((p) => p.visits.isNotEmpty || p.status == 'screening'),
        isTrue);
  });

  test('extractions.json parses into AiExtraction list with valid spans', () {
    final raw = _read('assets/data/extractions.json');
    final list = (raw['extractions'] as List)
        .map((e) => AiExtraction.fromJson(e as Map<String, dynamic>))
        .toList();
    expect(list.length, greaterThanOrEqualTo(40));
    for (final x in list) {
      expect(x.confidence, inInclusiveRange(0, 1));
      expect(x.spanStart, inInclusiveRange(0, x.sourceText.length));
      expect(x.spanEnd, inInclusiveRange(x.spanStart, x.sourceText.length));
      expect(x.sourceText.substring(x.spanStart, x.spanEnd), isNotEmpty);
    }
  });

  test('every real document text matches the embedded sourceText', () {
    final index = _read('assets/data/documents.json');
    final docs = (index['documents'] as List).cast<Map<String, dynamic>>();
    final extractions = (_read('assets/data/extractions.json')['extractions']
            as List)
        .cast<Map<String, dynamic>>();
    final textByDoc = <String, String>{};
    for (final doc in docs) {
      final id = doc['id'] as String;
      textByDoc[id] = File(doc['assetPath'] as String).readAsStringSync();
    }
    for (final x in extractions) {
      expect(x['sourceText'], textByDoc[x['documentId']],
          reason: 'embedded text drift in ${x['id']}');
    }
  });
}
