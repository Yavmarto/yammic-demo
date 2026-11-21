import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../api/fhir.dart';
import '../../data/session.dart';
import '../../theme/tokens.dart';
import '../../ui/download.dart';
import '../../ui/widgets.dart';
import 'export_builder.dart';

enum Fmt { odm, fhir }

class ExportScreen extends StatefulWidget {
  final FhirClient? fhir;
  const ExportScreen({super.key, this.fhir});
  @override
  State<ExportScreen> createState() => _ExportState();
}

class _ExportState extends State<ExportScreen> {
  late final FhirClient fhir = widget.fhir ?? FhirClient();
  Fmt fmt = Fmt.odm;
  int step = 0; // 0 choose, 1 generated
  bool busy = false;
  String? output, note, error;
  List<ExportRow> rows = [];
  int participants = 0;

  Future<void> _generate() async {
    final s = SessionScope.read(context);
    setState(() { busy = true; error = null; note = null; });
    try {
      final r = <ExportRow>[];
      final n = await s.run((a) async {
        final ps = await a.get('/participants') as List;
        for (final p in ps) {
          final e = await a.get('/participants/${p['id']}/ecrf') as Map;
          for (final f in (e['fields'] as List).cast<Map>().where((f) => f['value'] != null)) {
            r.add(ExportRow.from('${p['id']}', f));
          }
        }
        return ps.length;
      });
      rows = r;
      participants = n;
      output = fmt == Fmt.odm ? buildOdm('GBM-NL-2026-01', r) : prettyJson(buildFhirBundle(r));
      step = 1;
    } catch (e) {
      error = '$e';
    }
    if (mounted) setState(() => busy = false);
  }

  Future<void> _download() async {
    final name = fmt == Fmt.odm ? 'yammic-GBM-NL-2026-01.odm.xml' : 'yammic-GBM-NL-2026-01.fhir.json';
    final where = await saveFile(name, output!, fmt == Fmt.odm ? 'application/xml' : 'application/fhir+json');
    if (mounted) setState(() => note = 'Saved $where');
  }

  Future<void> _push() async {
    setState(() { busy = true; note = null; error = null; });
    try {
      final r = await fhir.push(buildFhirBundle(rows));
      final created = (r['entry'] as List? ?? []).where((e) => '${e['response']?['status']}'.startsWith('201')).length;
      note = 'Pushed to ${fhir.base}: $created created, ${rows.length - created} already present.';
    } catch (e) {
      error = 'Push failed: $e';
    }
    if (mounted) setState(() => busy = false);
  }

  @override
  Widget build(BuildContext context) {
    final s = SessionScope.of(context);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(K.s24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const PageHeader(title: 'Export', subtitle: 'Only human-verified eCRF values leave the platform. AI proposals are never exported.'),
        const SizedBox(height: K.s16),
        Row(children: [
          for (final (i, l) in ['Choose format', 'Validate and generate', 'Download or push'].indexed) ...[
            _stepDot(i, l),
            if (i < 2) const Expanded(child: Divider(indent: 8, endIndent: 8)),
          ],
        ]),
        const SizedBox(height: K.s16),
        LayoutBuilder(builder: (c, box) {
          final cards = Row(children: [
            Expanded(child: _formatCard(Fmt.odm, 'CDISC ODM 1.3.2', 'XML ClinicalData for the sponsor and regulators.', Icons.code)),
            const SizedBox(width: K.s16),
            Expanded(child: _formatCard(Fmt.fhir, 'FHIR R4 Bundle', 'Observation resources, pushable to the local HAPI server.', Icons.hub_outlined)),
          ]);
          return cards;
        }),
        const SizedBox(height: K.s16),
        Row(children: [
          WriteGate(
            blockedReason: s.isPi && !s.offline ? null : s.offline ? s.writeBlockedReason : 'Only the PI can generate an export.',
            builder: (en) => FilledButton.icon(
              onPressed: en && !busy ? _generate : null,
              icon: busy && step == 0 ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.rule, size: 18),
              label: const Text('Validate and generate'),
            ),
          ),
        ]),
        if (error != null) _msg(error!, Tone.bad, Icons.error_outline),
        if (step == 1 && output != null) ...[
          const SizedBox(height: K.s16),
          _validation(),
          const SizedBox(height: K.s16),
          Panel(
            title: 'Preview · ${fmt == Fmt.odm ? 'ODM XML' : 'FHIR Bundle'}',
            trailing: Row(mainAxisSize: MainAxisSize.min, children: [
              IconButton(tooltip: 'Copy', icon: const Icon(Icons.copy, size: 18), onPressed: () => Clipboard.setData(ClipboardData(text: output!))),
              OutlinedButton.icon(onPressed: _download, icon: const Icon(Icons.download, size: 18), label: const Text('Download')),
              if (fmt == Fmt.fhir) ...[
                const SizedBox(width: 8),
                FilledButton.icon(onPressed: busy || rows.isEmpty ? null : _push, icon: const Icon(Icons.upload, size: 18), label: const Text('Push to FHIR server')),
              ],
            ]),
            child: Container(
              constraints: const BoxConstraints(maxHeight: 360),
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: K.bg, borderRadius: BorderRadius.circular(8), border: Border.all(color: K.line)),
              child: SingleChildScrollView(child: SelectableText(output!.length > 6000 ? '${output!.substring(0, 6000)}\n… (${output!.length - 6000} more characters in the download)' : output!, key: const ValueKey('export-output'), style: K.mono.copyWith(color: K.ink))),
            ),
          ),
          if (note != null) _msg(note!, Tone.info, Icons.check_circle_outline),
        ],
      ]),
    );
  }

  Widget _msg(String t, Tone tone, IconData i) {
    final (bg, line, ink) = toneColors(tone);
    return Container(
      margin: const EdgeInsets.only(top: K.s12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(8), border: Border.all(color: line)),
      child: Row(children: [Icon(i, size: 18, color: ink), const SizedBox(width: 8), Expanded(child: Text(t, style: K.small.copyWith(color: ink, fontWeight: FontWeight.w500)))]),
    );
  }

  Widget _validation() {
    final sdv = rows.where((r) => r.sdvAt != null).length;
    final checks = [
      (rows.isNotEmpty, '${rows.length} verified values from $participants participants'),
      (rows.every((r) => r.verifiedBy.isNotEmpty), 'Every value has a named verifier'),
      (sdv == rows.length && rows.isNotEmpty, '$sdv of ${rows.length} values source-data verified'),
    ];
    return Panel(
      title: 'Validation',
      child: Column(children: [
        for (final c in checks)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Row(children: [
              Icon(c.$1 ? Icons.check_circle_outline : Icons.warning_amber_rounded, size: 16, color: c.$1 ? K.okInk : K.aiInk),
              const SizedBox(width: 8),
              Text(c.$2, style: K.body.copyWith(fontSize: 13)),
            ]),
          ),
        if (rows.isEmpty)
          Padding(padding: const EdgeInsets.only(top: 8), child: Text('Nothing verified yet. Review AI proposals first, then export.', style: K.small.copyWith(color: K.aiInk))),
      ]),
    );
  }

  Widget _stepDot(int i, String l) => Row(mainAxisSize: MainAxisSize.min, children: [
        CircleAvatar(radius: 11, backgroundColor: i <= step ? K.accent : K.line, child: Text('${i + 1}', style: TextStyle(fontSize: 11, color: i <= step ? Colors.white : K.ink3, fontWeight: FontWeight.w500))),
        const SizedBox(width: 8),
        Text(l, style: K.small.copyWith(color: i <= step ? K.ink : K.ink3)),
      ]);

  Widget _formatCard(Fmt f, String t, String hint, IconData icon) {
    final sel = fmt == f;
    return Semantics(
      button: true,
      selected: sel,
      child: InkWell(
        key: ValueKey('fmt-${f.name}'),
        borderRadius: BorderRadius.circular(12),
        onTap: () => setState(() { fmt = f; step = 0; output = null; note = null; }),
        child: Container(
          padding: const EdgeInsets.all(K.s16),
          decoration: BoxDecoration(color: sel ? K.accentSoft : K.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: sel ? K.accent : K.line, width: sel ? 2 : 1)),
          child: Row(children: [
            Icon(icon, color: sel ? K.accent : K.ink2),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(t, style: K.heading), Text(hint, style: K.small)])),
            if (sel) const Icon(Icons.check_circle, color: K.accent, size: 20),
          ]),
        ),
      ),
    );
  }
}
