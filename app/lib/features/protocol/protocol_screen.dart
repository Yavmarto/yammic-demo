import 'package:flutter/material.dart';
import '../../data/session.dart';
import '../../theme/tokens.dart';
import '../../ui/async.dart';
import '../../ui/format.dart';
import '../../ui/widgets.dart';
import '../dashboard/dashboard_screen.dart' show studyId;

Pill versionPill(String status) => switch (status) {
      'approved' => const Pill('Active', tone: Tone.ok, icon: Icons.check_circle_outline),
      'proposed' => const Pill('Draft · AI proposal', tone: Tone.ai, icon: Icons.auto_awesome),
      _ => Pill(status == 'superseded' ? 'Superseded' : status, tone: Tone.muted),
    };

/// Protocol → form: the AI reads the protocol and proposes a form version; only the PI approves it.
class ProtocolScreen extends StatefulWidget {
  const ProtocolScreen({super.key});
  @override
  State<ProtocolScreen> createState() => _ProtocolScreenState();
}

class _ProtocolScreenState extends State<ProtocolScreen> {
  int? sel;
  int rev = 0;
  bool busy = false;

  Future<void> _post(String path, [Object? body]) async {
    final s = SessionScope.read(context);
    setState(() => busy = true);
    try {
      final r = await s.api.post(path, body);
      sel = (r as Map)['version'] as int;
      rev++;
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _approve(Map v) async {
    final note = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text('Approve version ${v['version']}?'),
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('This makes it the active form and entry criteria. The approval is written to the audit trail. Values already captured keep their own form version.', style: K.small.copyWith(fontSize: 13.5)),
          const SizedBox(height: K.s12),
          TextField(key: const Key('approve-note'), controller: note, decoration: const InputDecoration(labelText: 'Note (optional)')),
        ]),
        actions: [TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Cancel')), FilledButton(key: const Key('approve-confirm'), onPressed: () => Navigator.pop(c, true), child: const Text('Approve'))],
      ),
    );
    if (ok == true) await _post('/studies/$studyId/forms/${v['version']}/approve', {if (note.text.trim().isNotEmpty) 'note': note.text.trim()});
  }

  @override
  Widget build(BuildContext context) {
    final s = SessionScope.of(context);
    return Loader<List>(
      key: ValueKey(rev),
      load: (s) => s.run((a) async => await a.get('/studies/$studyId/forms') as List),
      builder: (c, list, reload) {
        final versions = [for (final x in list) Map<String, dynamic>.from(x as Map)];
        final v = versions.where((x) => x['version'] == sel).firstOrNull ?? versions.firstOrNull;
        final canPropose = !s.offline && (s.role == 'pi' || s.role == 'nurse');
        return ListView(padding: const EdgeInsets.all(K.s24), children: [
          PageHeader(
            title: 'Protocol → form',
            subtitle: 'The AI reads the protocol synopsis and proposes form fields and entry criteria. The PI approves.',
            trailing: WriteGate(
              blockedReason: s.offline ? 'Reconnect the local backend to write.' : canPropose ? null : 'Monitor role cannot analyse the protocol.',
              builder: (en) => FilledButton.icon(key: const Key('analyse'), onPressed: en && !busy ? () => _post('/studies/$studyId/forms/propose') : null, icon: const Icon(Icons.auto_awesome, size: 16), label: Text(busy ? 'Analysing…' : 'Analyse protocol')),
            ),
          ),
          const SizedBox(height: K.s16),
          if (v == null)
            const Panel(child: EmptyState(icon: Icons.account_tree_outlined, title: 'No form versions yet', hint: 'Analyse the protocol to get a first proposal.'))
          else
            LayoutBuilder(builder: (c, box) {
              final list = Panel(
                title: 'Versions',
                padding: EdgeInsets.zero,
                child: Column(children: [
                  for (final x in versions)
                    DataRow2(
                      key: Key('ver-${x['version']}'),
                      flex: const [2, 5],
                      selected: x['version'] == v['version'],
                      onTap: () => setState(() => sel = x['version'] as int),
                      cells: [Text('v${x['version']}', style: numStyle), Align(alignment: Alignment.centerLeft, child: versionPill('${x['status']}'))],
                    ),
                ]),
              );
              final detail = _Detail(v: v, s: s, onApprove: () => _approve(v));
              return box.maxWidth >= 1000
                  ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [SizedBox(width: 280, child: list), const SizedBox(width: K.s16), Expanded(child: detail)])
                  : Column(children: [list, const SizedBox(height: K.s16), detail]);
            }),
        ]);
      },
    );
  }
}

class _Detail extends StatelessWidget {
  final Map v;
  final Session s;
  final VoidCallback onApprove;
  const _Detail({required this.v, required this.s, required this.onApprove});
  @override
  Widget build(BuildContext context) {
    final fields = (v['fields'] as List).cast<Map>(), crit = (v['criteria'] as List).cast<Map>();
    final proposed = v['status'] == 'proposed';
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Panel(
        child: Row(children: [
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Wrap(spacing: 10, crossAxisAlignment: WrapCrossAlignment.center, children: [Text('${v['formId']} · v${v['version']}', style: K.title), versionPill('${v['status']}')]),
              const SizedBox(height: 4),
              Text(
                proposed
                    ? 'Proposed by ${v['proposedBy']} (${v['provider'] ?? 'rules'}/${v['model'] ?? ''}) · ${fmtDateTime(v['proposedAt'])}'
                    : v['approvedBy'] != null ? 'Approved by ${v['approvedBy']} · ${fmtDateTime(v['approvedAt'])}' : 'Proposed by ${v['proposedBy']}',
                style: K.small,
              ),
              if (v['note'] != null) Text('Note: ${v['note']}', style: K.small),
            ]),
          ),
          if (proposed)
            WriteGate(
              blockedReason: s.offline ? 'Reconnect the local backend to write.' : s.isPi ? null : 'Only the PI can approve a form version.',
              builder: (en) => FilledButton(key: const Key('approve'), onPressed: en ? onApprove : null, child: const Text('Approve version')),
            ),
        ]),
      ),
      const SizedBox(height: K.s16),
      Panel(
        title: 'Form fields (${fields.length})',
        padding: EdgeInsets.zero,
        child: Column(children: [
          const TableHead([('Field', 3, false), ('Section', 2, false), ('Type', 2, false), ('Required', 1, false), ('Protocol sentence', 6, false)]),
          for (final f in fields)
            DataRow2(flex: const [3, 2, 2, 1, 6], cells: [
              Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [Text('${f['label']}', style: K.body), Text('${f['id']}', style: K.mono)]),
              Text('${f['section'] ?? '—'}', style: K.small),
              Text('${f['valueType'] ?? '—'}${f['unit'] != null ? ' · ${f['unit']}' : ''}', style: K.small),
              Text(f['required'] == true ? 'Yes' : 'No', style: K.small),
              Text('${f['sourceSentence'] ?? f['help'] ?? ''}', maxLines: 2, overflow: TextOverflow.ellipsis, style: K.small),
            ]),
        ]),
      ),
      const SizedBox(height: K.s16),
      Panel(
        title: 'Entry criteria (${crit.length})',
        padding: EdgeInsets.zero,
        child: Column(children: [
          const TableHead([('ID', 1, false), ('Type', 2, false), ('Criterion', 9, false)]),
          for (final k in crit) DataRow2(flex: const [1, 2, 9], cells: [Text('${k['id']}', style: K.mono), Text('${k['type']}', style: K.small), Text('${k['text']}', style: K.body)]),
        ]),
      ),
    ]);
  }
}
