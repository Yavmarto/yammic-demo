import 'package:flutter/material.dart';
import '../../api/api.dart';
import '../../data/session.dart';
import '../../theme/tokens.dart';
import '../../ui/async.dart';
import '../../ui/format.dart';
import '../../ui/widgets.dart';

class _Data {
  final Map? fhir;
  final List runs;
  _Data(this.fhir, this.runs);
}

Future<_Data> _load(Session s) => s.run((a) async {
      final list = await a.get('/integrations') as List;
      final runs = await a.get('/integrations/fhir/runs', query: {'limit': '10'}) as List;
      return _Data(list.cast<Map>().where((x) => x['id'] == 'fhir').firstOrNull, runs);
    });

class IntegrationsScreen extends StatelessWidget {
  const IntegrationsScreen({super.key});
  @override
  Widget build(BuildContext context) => Loader<_Data>(
        load: _load,
        builder: (c, d, reload) => _Body(d, reload),
      );
}

class _Body extends StatefulWidget {
  final _Data d;
  final VoidCallback reload;
  const _Body(this.d, this.reload);
  @override
  State<_Body> createState() => _BodyState();
}

class _BodyState extends State<_Body> {
  bool syncing = false, full = false;
  String? error;
  Map? result;

  Future<void> _sync() async {
    final s = SessionScope.read(context);
    setState(() { syncing = true; error = null; result = null; });
    try {
      // Show the steps for at least a moment so the work is visible, then call the backend.
      final r = await s.api.post('/integrations/fhir/sync${full ? '?full=true' : ''}') as Map;
      if (!mounted) return;
      result = r;
      widget.reload();
    } on ApiException catch (e) {
      error = e.message;
    } on Unreachable catch (e) {
      s.markOffline();
      error = e.message;
    }
    if (mounted) setState(() => syncing = false);
  }

  @override
  Widget build(BuildContext context) {
    final s = SessionScope.of(context);
    final f = widget.d.fhir;
    final state = '${f?['status'] ?? 'unreachable'}';
    final ok = state == 'connected';
    final blocked = s.offline || s.role == 'monitor' ? s.writeBlockedReason : null;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(K.s24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        PageHeader(
          title: 'Integrations',
          subtitle: 'Hospital data arrives over FHIR R4, is pseudonymised, then becomes participants, documents and AI proposals.',
          trailing: Row(mainAxisSize: MainAxisSize.min, children: [
            Row(mainAxisSize: MainAxisSize.min, children: [
              Checkbox(value: full, onChanged: syncing ? null : (v) => setState(() => full = v ?? false)),
              Text('Full re-sync', style: K.small.copyWith(color: K.ink)),
            ]),
            const SizedBox(width: 12),
            WriteGate(
              blockedReason: blocked,
              builder: (en) => FilledButton.icon(
                onPressed: en && !syncing ? _sync : null,
                icon: syncing ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.sync, size: 18),
                label: Text(syncing ? 'Syncing…' : 'Sync now'),
              ),
            ),
          ]),
        ),
        const SizedBox(height: K.s16),
        Panel(
          title: f == null ? 'Hospital EHR (FHIR R4)' : '${f['name']}',
          trailing: ok ? const Pill('Connected', tone: Tone.info, icon: Icons.link) : const Pill('Unreachable', tone: Tone.bad, icon: Icons.link_off),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (!ok)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text('${f?['error'] ?? 'FHIR server not reachable'}. Start it with `make up`, then retry.', style: K.small.copyWith(color: K.badInk)),
              ),
            Wrap(spacing: K.s32, runSpacing: 12, children: [
              _kv('Endpoint', '${f?['baseUrl'] ?? '—'}'),
              _kv('FHIR version', '${f?['fhirVersion'] ?? '—'}'),
              _kv('Server', '${f?['software'] ?? '—'} ${f?['softwareVersion'] ?? ''}'.trim()),
              _kv('Pseudonymised patients', '${f?['pseudonymisedPatients'] ?? '—'}'),
              _kv('Last sync', f?['lastSync'] == null ? 'never' : fmtDateTime(f!['lastSync']['startedAt'])),
            ]),
            if (syncing) ...[const SizedBox(height: K.s16), const LinearProgressIndicator(minHeight: 2), const SizedBox(height: 6), Text('Pulling from the FHIR server, pseudonymising, queueing AI extraction…', style: K.small)],
            if (error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(error!, style: K.small.copyWith(color: K.badInk))),
            if (result != null) Padding(padding: const EdgeInsets.only(top: 12), child: _resultLine(result!)),
          ]),
        ),
        const SizedBox(height: K.s16),
        _runs(),
      ]),
    );
  }

  Widget _resultLine(Map r) {
    final c = (r['counts'] as Map?) ?? {};
    final fetched = c.entries.where((e) => e.value is Map && (e.value as Map).containsKey('fetched')).fold<int>(0, (a, e) => a + ((e.value['fetched'] as num?)?.toInt() ?? 0));
    return Row(children: [
      Icon(r['status'] == 'failed' ? Icons.error_outline : Icons.check_circle_outline, size: 16, color: r['status'] == 'failed' ? K.badInk : K.infoInk),
      const SizedBox(width: 8),
      Expanded(child: Text('Sync ${r['status']}: $fetched resources fetched, ${c['documents']?['created'] ?? 0} new documents, ${c['extractionRuns']?['queued'] ?? 0} extraction runs queued.', style: K.small.copyWith(color: K.ink, fontWeight: FontWeight.w500))),
    ]);
  }

  Widget _kv(String k, String v) => Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
        Text(k.toUpperCase(), style: K.label),
        const SizedBox(height: 2),
        Text(v, style: K.mono.copyWith(color: K.ink, fontSize: 13)),
      ]);

  Widget _runs() {
    final runs = widget.d.runs.cast<Map>();
    int created(Map r) => ((r['counts'] as Map?) ?? {}).entries.fold<int>(0, (a, e) => a + (e.value is Map ? ((e.value['created'] as num?)?.toInt() ?? 0) : 0));
    return Panel(
      title: 'Sync runs',
      padding: EdgeInsets.zero,
      child: runs.isEmpty
          ? const SizedBox(height: 220, child: EmptyState(icon: Icons.sync, title: 'No sync runs yet', hint: 'Press Sync now to pull the hospital FHIR server into the platform.'))
          : Column(children: [
              const TableHead([('Run', 1, false), ('Started', 3, false), ('Mode', 2, false), ('Status', 2, false), ('Created', 2, true), ('Duration', 2, true), ('By', 2, false)]),
              for (final r in runs)
                DataRow2(
                  key: ValueKey('run-${r['id']}'),
                  height: 40,
                  flex: const [1, 3, 2, 2, 2, 2, 2],
                  cells: [
                    Text('#${r['id']}', style: K.mono),
                    Text(fmtDateTime(r['startedAt']), style: K.mono),
                    Text('${r['mode']}', style: K.small),
                    Align(alignment: Alignment.centerLeft, child: Pill(r['status'] == 'completed' ? 'Completed' : r['status'] == 'failed' ? 'Failed' : '${r['status']}', tone: r['status'] == 'completed' ? Tone.info : r['status'] == 'failed' ? Tone.bad : Tone.ai)),
                    Text('${created(r)}', textAlign: TextAlign.right, style: numStyle),
                    Text(r['durationMs'] == null ? '—' : '${r['durationMs']} ms', textAlign: TextAlign.right, style: K.mono),
                    Text('${r['triggeredBy']}', style: K.small, overflow: TextOverflow.ellipsis),
                  ],
                ),
            ]),
    );
  }
}
