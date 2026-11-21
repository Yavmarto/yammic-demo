import 'dart:convert';

String _x(Object? v) => '$v'.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');

/// One verified eCRF value, flattened for export.
class ExportRow {
  final String participantId, field, label, value, verifiedBy, verifiedAt;
  final String? unit, codeSystem, code, sdvAt;
  ExportRow(this.participantId, this.field, this.label, this.value, this.verifiedBy, this.verifiedAt, {this.unit, this.codeSystem, this.code, this.sdvAt});

  factory ExportRow.from(String pid, Map f) {
    final v = f['value'] as Map;
    final c = v['code'] as Map?;
    return ExportRow(pid, '${f['id']}', '${f['label']}', '${v['value']}', '${v['verifiedBy']}', '${v['verifiedAt']}',
        unit: f['unit'] as String?, codeSystem: c?['system'] as String?, code: c?['code'] as String?, sdvAt: v['sdvAt'] as String?);
  }
}

/// CDISC ODM 1.3.2 ClinicalData: only human-verified values are ever exported.
String buildOdm(String studyId, List<ExportRow> rows, {String createdAt = '2026-11-23T09:00:00Z'}) {
  final b = StringBuffer()
    ..writeln('<?xml version="1.0" encoding="UTF-8"?>')
    ..writeln('<!-- Synthetic data: prototype, not for clinical use -->')
    ..writeln('<ODM xmlns="http://www.cdisc.org/ns/odm/v1.3" ODMVersion="1.3.2" FileType="Snapshot" FileOID="YAMMIC-$studyId" CreationDateTime="$createdAt">')
    ..writeln('  <ClinicalData StudyOID="${_x(studyId)}" MetaDataVersionOID="v1">');
  final byP = <String, List<ExportRow>>{};
  for (final r in rows) {
    byP.putIfAbsent(r.participantId, () => []).add(r);
  }
  for (final e in byP.entries) {
    b
      ..writeln('    <SubjectData SubjectKey="${_x(e.key)}">')
      ..writeln('      <StudyEventData StudyEventOID="BASELINE">')
      ..writeln('        <FormData FormOID="ECRF-GBM-BASELINE">')
      ..writeln('          <ItemGroupData ItemGroupOID="IG.MAIN">');
    for (final r in e.value) {
      b.writeln('            <ItemData ItemOID="${_x(r.field)}" Value="${_x(r.value)}"${r.unit != null ? ' MeasurementUnitOID="${_x(r.unit)}"' : ''}/>');
    }
    b
      ..writeln('          </ItemGroupData>')
      ..writeln('        </FormData>')
      ..writeln('      </StudyEventData>')
      ..writeln('    </SubjectData>');
  }
  b
    ..writeln('  </ClinicalData>')
    ..writeln('</ODM>');
  return b.toString();
}

/// FHIR R4 transaction Bundle of Observations, conditional-create so a re-push never duplicates.
Map<String, dynamic> buildFhirBundle(List<ExportRow> rows) => {
      'resourceType': 'Bundle',
      'type': 'transaction',
      'entry': [
        for (final r in rows)
          {
            'fullUrl': 'urn:uuid:${r.participantId}-${r.field}',
            'resource': {
              'resourceType': 'Observation',
              'status': 'final',
              'identifier': [{'system': 'urn:yammic:ecrf', 'value': '${r.participantId}/${r.field}'}],
              'code': {
                'text': r.label,
                'coding': [if (r.code != null) {'system': r.codeSystem, 'code': r.code}],
              },
              'subject': {'display': r.participantId, 'identifier': {'system': 'urn:yammic:participant', 'value': r.participantId}},
              'valueString': r.unit == null ? r.value : '${r.value} ${r.unit}',
              'performer': [{'display': r.verifiedBy}],
              'meta': {'tag': [{'system': 'urn:yammic', 'code': 'synthetic-export'}]},
            },
            'request': {'method': 'POST', 'url': 'Observation', 'ifNoneExist': 'identifier=urn:yammic:ecrf|${r.participantId}/${r.field}'},
          },
      ],
    };

String prettyJson(Object o) => const JsonEncoder.withIndent('  ').convert(o);
