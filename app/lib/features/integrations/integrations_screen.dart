import 'package:flutter/material.dart';
import '../../api/fhir.dart';
import '../../data/session.dart';
import '../../theme/tokens.dart';
import '../../ui/format.dart';
import '../../ui/widgets.dart';

const fhirTypes = ['Patient', 'Encounter', 'Condition', 'MedicationRequest', 'Observation', 'DocumentReference'];

/// Sync history lives for the app session (the backend has no sync endpoint yet).
final syncRuns = <Map<String, dynamic>>[];

class IntegrationsScreen extends StatefulWidget {
  final FhirClient? fhir;
  const IntegrationsScreen({super.key, this.fhir});
  @override
  State<IntegrationsScreen> createState() => _IntegrationsState();
}

class _IntegrationsState extends State<IntegrationsScreen> {
  late final FhirClient fhir = widget.fhir ?? FhirClient();
  Map? meta;
  Map<String, int> counts = {};
  int? platformParticipants;
  String? error;
  bool busy = true;
  int? latency;
  int _step = -1;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _refresh());
  }

  Future<void> _refresh() async {
    setState(() { busy = true; error = null; });
    final s = SessionScope.read(context);
    final sw = Stopwatch()..start();
    try {
      meta = await fhir.metadata();
      latency = sw.elapsedMilliseconds;
      final c = <String, int>{};
      for (final t in fhirTypes) {
        c[t] = await fhir.count(t);
      }
      counts = c;
      platformParticipants = (await s.run((a) async => await a.get('/participants') as List)).length;
    } catch (e) {
      error = '$e';
      meta = null;
    }
    if (mounted) setState(() => busy = false);
  }

  Future<void> _sync() async {
    final started = DateTime.now();
    for (var i = 0; i < 3; i++) {
      setState(() => _step = i);
      await Future.delayed(const Duration(milliseconds: 450));
      if (i == 1) await _refresh();
    }
    final ok = error == null;
    syncRuns.insert(0, {
      'at': started.toIso8601String(),
      'status': ok ? 'ok' : 'failed',
      'resources': counts.values.fold<int>(0, (a, b) => a + b),
      'patients': counts['Patient'] ?? 0,
      'matched': platformParticipants == counts['Patient'],
      'ms': DateTime.now().difference(started).inMilliseconds,
    });
    if (mounted) setState(() => _step = -1);
  }

  @override
  Widget build(BuildContext context) {
    final s = SessionScope.of(context);
    final ok = meta != null;
    final blocked = s.offline ? s.writeBlockedReason : s.isMonitor ? s.writeBlockedReason : null;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(K.s24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        PageHeader(
          title: 'Integrations',
          subtitle: 'Hospital data arrives over FHIR R4, then becomes participants, documents and AI proposals.',
          trailing: WriteGate(
            blockedReason: blocked,
            builder: (en) => FilledButton.icon(
              onPressed: en && _step < 0 && !busy ? _sync : null,
              icon: const Icon(Icons.sync, size: 18),
              label: Text(_step >= 0 ? 'Syncing…' : 'Sync now'),
            ),
          ),
        ),
        const SizedBox(height: K.s16),
        Panel(
          title: 'HAPI FHIR R4 · local',
          trailing: busy
              ? const Pill('Checking', tone: Tone.ai, icon: Icons.sync)
              : ok
                  ? Pill('Connected${latency != null ? ' · $latency ms' : ''}', tone: Tone.muted, icon: Icons.link)
                  : const Pill('Unreachable', tone: Tone.bad, icon: Icons.link_off),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (!busy && !ok)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text('${error ?? 'FHIR server not reachable'}. Start it with `make up`, then retry.', style: K.small.copyWith(color: K.badInk)),
              ),
            Wrap(spacing: K.s32, runSpacing: 8, children: [
              _kv('Endpoint', fhir.base),
              _kv('FHIR version', '${meta?['fhirVersion'] ?? '—'}'),
              _kv('Server', '${meta?['software']?['name'] ?? '—'} ${meta?['software']?['version'] ?? ''}'),
              _kv('Platform participants', platformParticipants?.toString() ?? '—'),
            ]),
            if (!busy && !ok) TextButton(onPressed: _refresh, child: const Text('Retry connection')),
            if (_step >= 0) ...[
              const SizedBox(height: K.s16),
              _steps(),
            ],
          ]),
        ),
        const SizedBox(height: K.s16),
        LayoutBuilder(builder: (c, box) {
          final res = _resources();
          final runs = _runs();
          return box.maxWidth >= 1000
              ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(flex: 5, child: res), const SizedBox(width: K.s16), Expanded(flex: 7, child: runs)])
              : Column(children: [res, const SizedBox(height: K.s16), runs]);
        }),
      ]),
    );
  }

  Widget _kv(String k, String v) => Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
        Text(k.toUpperCase(), style: K.label),
        const SizedBox(height: 2),
        Text(v, style: K.mono.copyWith(color: K.ink, fontSize: 13)),
      ]);

  Widget _steps() {
    const names = ['Connect to FHIR server', 'Read resources', 'Reconcile with platform'];
    return Column(children: [
      for (var i = 0; i < names.length; i++)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 3),
          child: Row(children: [
            Icon(i < _step ? Icons.check_circle_outline : i == _step ? Icons.sync : Icons.radio_button_unchecked, size: 16, color: i <= _step ? K.accent : K.ink3),
            const SizedBox(width: 8),
            Text(names[i], style: K.small.copyWith(color: i <= _step ? K.ink : K.ink3)),
          ]),
        ),
      const SizedBox(height: 6),
      const LinearProgressIndicator(minHeight: 2),
    ]);
  }

  Widget _resources() => Panel(
        title: 'Resources on the server',
        padding: EdgeInsets.zero,
        child: Column(children: [
          const TableHead([('Resource', 4, false), ('Count', 2, true)]),
          if (counts.isEmpty)
            const Padding(padding: EdgeInsets.all(K.s16), child: Text('No data read yet.', style: K.small))
          else
            for (final t in fhirTypes)
              DataRow2(height: 40, flex: const [4, 2], cells: [Text(t, style: K.body.copyWith(fontSize: 13)), Text('${counts[t] ?? 0}', textAlign: TextAlign.right, style: numStyle)]),
        ]),
      );

  Widget _runs() => Panel(
        title: 'Sync runs',
        padding: EdgeInsets.zero,
        child: syncRuns.isEmpty
            ? const SizedBox(height: 140, child: EmptyState(icon: Icons.sync, title: 'No sync runs yet', hint: 'Press Sync now to read the hospital FHIR server and reconcile it with the platform.'))
            : Column(children: [
                const TableHead([('Started', 4, false), ('Status', 2, false), ('Resources', 2, true), ('Patients', 2, true), ('Duration', 2, true)]),
                for (final r in syncRuns)
                  DataRow2(height: 40, flex: const [4, 2, 2, 2, 2], cells: [
                    Text(fmtDateTime(r['at']), style: K.mono),
                    Align(alignment: Alignment.centerLeft, child: Pill(r['status'] == 'ok' ? (r['matched'] == true ? 'In sync' : 'Differs') : 'Failed', tone: r['status'] == 'ok' ? (r['matched'] == true ? Tone.info : Tone.ai) : Tone.bad)),
                    Text('${r['resources']}', textAlign: TextAlign.right, style: numStyle),
                    Text('${r['patients']}', textAlign: TextAlign.right, style: numStyle),
                    Text('${r['ms']} ms', textAlign: TextAlign.right, style: K.mono),
                  ]),
              ]),
      );
}
