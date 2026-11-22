import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../api/api.dart';
import '../../data/session.dart';
import '../../theme/tokens.dart';
import '../../ui/download.dart';
import '../../ui/widgets.dart';

enum Fmt { odm, fhir }

const _studyId = 'GBM-NL-2026-01';

class ExportScreen extends StatefulWidget {
  const ExportScreen({super.key});
  @override
  State<ExportScreen> createState() => _ExportState();
}

class _ExportState extends State<ExportScreen> {
  Fmt fmt = Fmt.odm;
  bool busy = false;
  String? output, note, error, noteTone;
  List participants = [];
  String? pid;
  Session? s;
  Map? synthetic;
  String? deliveryState;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (s == null) {
      s = SessionScope.read(context);
      s!.run((a) async => await a.get('/participants') as List).then((p) {
        if (mounted) setState(() { participants = p; pid ??= p.cast<Map>().where((x) => (x['ecrfVerified'] as int) > 0).map((x) => x['id'] as String).firstOrNull ?? (p.isEmpty ? null : p.first['id']); });
      }).catchError((_) {});
    }
  }

  Future<void> _generate() async {
    setState(() { busy = true; error = null; note = null; });
    try {
      // Raw body: ODM is XML, FHIR is JSON; the backend audits each export.
      final r = fmt == Fmt.odm ? await s!.http.getText('/studies/$_studyId/export/odm') : await s!.http.getText('/participants/$pid/export/fhir');
      output = r;
    } on ApiException catch (e) {
      error = e.message;
    } on Unreachable catch (e) {
      s!.markOffline();
      error = e.message;
    }
    if (mounted) setState(() => busy = false);
  }

  Future<void> _download() async {
    final name = fmt == Fmt.odm ? '$_studyId-odm-1.3.2.xml' : '$pid-fhir-bundle.json';
    final where = await saveFile(name, output!, fmt == Fmt.odm ? 'application/xml' : 'application/fhir+json');
    if (mounted) setState(() { note = 'Saved $where'; noteTone = 'ok'; });
  }

  Future<void> _push() async {
    setState(() { busy = true; note = null; error = null; });
    try {
      final r = await s!.api.post('/participants/$pid/export/fhir/push') as Map;
      note = 'Pushed to the FHIR server: ${r['pushed']} resources written.';
      noteTone = 'ok';
    } on ApiException catch (e) {
      error = e.message;
    } on Unreachable catch (e) {
      error = e.message;
    }
    if (mounted) setState(() => busy = false);
  }

  Future<void> _synthetic({bool send = false}) async {
    setState(() { busy = true; error = null; if (!send) { synthetic = null; deliveryState = null; } });
    try {
      if (send) {
        final result = await s!.api.post('/participants/GBM-NL-001/export/synthetic-writeback', {'deliveryId': synthetic!['deliveryId']}) as Map;
        deliveryState = "Delivered. ${result['retryState']}";
      } else {
        synthetic = await s!.api.get('/participants/GBM-NL-001/export/synthetic-writeback') as Map;
        deliveryState = 'Ready to send.';
      }
    } on ApiException catch (e) {
      deliveryState = send ? 'Delivery not confirmed. Retry the same reviewed value.' : null;
      error = e.message;
    } on Unreachable catch (e) {
      deliveryState = send ? 'Delivery not confirmed. Retry the same reviewed value.' : null;
      error = e.message;
    }
    if (mounted) setState(() => busy = false);
  }

  @override
  Widget build(BuildContext context) {
    final s = SessionScope.of(context);
    final step = output != null ? 2 : busy ? 1 : 0;
    final blocked = s.offline ? s.writeBlockedReason : s.role == 'nurse' ? 'Export is for the PI and monitor roles.' : null;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(K.s24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const PageHeader(title: 'Export', subtitle: 'Only human-verified eCRF values leave the platform. AI proposals are never exported. Every export is audited.'),
        const SizedBox(height: K.s16),
        Panel(title: 'Local synthetic write-back · GBM-NL-001', child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Review one KPS value for the simulated receiver. This demo does not establish the FR-063 policy.'),
          const SizedBox(height: 8),
          WriteGate(blockedReason: blocked, builder: (en) => OutlinedButton(onPressed: en && !busy ? () => _synthetic() : null, child: const Text('Review synthetic delivery'))),
          if (synthetic != null) ...[
            SelectableText('Destination: ${synthetic!['destination_field']}\n${synthetic!['review_state']} value: ${synthetic!['value']}\nSource document ID: ${synthetic!['source_id']}\nExtraction ID: ${synthetic!['extraction_id']}'),
            Text(deliveryState ?? ''),
            FilledButton(onPressed: busy ? null : () => _synthetic(send: true), child: Text(deliveryState == 'Ready to send.' ? 'Send reviewed value' : 'Retry delivery')),
          ],
        ])),
        const SizedBox(height: K.s16),
        Row(children: [
          for (final (i, l) in ['Choose format', 'Generate', 'Download or push'].indexed) ...[
            _stepDot(i, l, step),
            if (i < 2) const Expanded(child: Divider(indent: 8, endIndent: 8)),
          ],
        ]),
        const SizedBox(height: K.s16),
        Row(children: [
          Expanded(child: _formatCard(Fmt.odm, 'CDISC ODM 1.3.2', 'Study-wide XML snapshot with audit records, for sponsors and regulators.', Icons.code)),
          const SizedBox(width: K.s16),
          Expanded(child: _formatCard(Fmt.fhir, 'FHIR R4 bundle', 'Per participant: QuestionnaireResponse, Provenance (AI vs human), AuditEvents.', Icons.hub_outlined)),
        ]),
        const SizedBox(height: K.s16),
        Wrap(spacing: 12, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
          if (fmt == Fmt.fhir)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(color: K.surface, border: Border.all(color: K.lineStrong), borderRadius: BorderRadius.circular(8)),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: pid,
                  hint: const Text('Participant'),
                  items: [for (final p in participants) DropdownMenuItem(value: '${p['id']}', child: Text('${p['id']} · ${p['ecrfVerified']} verified'))],
                  onChanged: (v) => setState(() { pid = v; output = null; note = null; }),
                ),
              ),
            ),
          WriteGate(
            blockedReason: blocked,
            builder: (en) => FilledButton.icon(
              onPressed: en && !busy && (fmt == Fmt.odm || pid != null) ? _generate : null,
              icon: busy ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.rule, size: 18),
              label: const Text('Generate export'),
            ),
          ),
        ]),
        if (error != null) _msg(error!, Tone.bad, Icons.error_outline),
        if (output != null) ...[
          const SizedBox(height: K.s16),
          Panel(
            title: 'Preview · ${fmt == Fmt.odm ? 'ODM XML' : 'FHIR bundle'} · ${output!.length} characters',
            trailing: Wrap(spacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
              IconButton(tooltip: 'Copy', icon: const Icon(Icons.copy, size: 18), onPressed: () => Clipboard.setData(ClipboardData(text: output!))),
              OutlinedButton.icon(onPressed: _download, icon: const Icon(Icons.download, size: 18), label: const Text('Download')),
              if (fmt == Fmt.fhir) FilledButton.icon(onPressed: busy ? null : _push, icon: const Icon(Icons.upload, size: 18), label: const Text('Push to FHIR server')),
            ]),
            child: Container(
              constraints: const BoxConstraints(maxHeight: 380),
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: K.bg, borderRadius: BorderRadius.circular(8), border: Border.all(color: K.line)),
              child: SingleChildScrollView(child: SelectableText(output!.length > 8000 ? '${output!.substring(0, 8000)}\n… ${output!.length - 8000} more characters in the download' : output!, key: const ValueKey('export-output'), style: K.mono.copyWith(color: K.ink))),
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

  Widget _stepDot(int i, String l, int step) => Row(mainAxisSize: MainAxisSize.min, children: [
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
        onTap: () => setState(() { fmt = f; output = null; note = null; error = null; }),
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
