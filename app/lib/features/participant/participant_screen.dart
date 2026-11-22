import 'package:flutter/material.dart';
import '../../data/session.dart';
import '../../theme/tokens.dart';
import '../../ui/async.dart';
import '../../ui/format.dart';
import '../../ui/widgets.dart';

void _go(BuildContext c, String r, [Object? a]) => Navigator.of(c).pushReplacementNamed(r, arguments: a);

class ParticipantListScreen extends StatefulWidget {
  const ParticipantListScreen({super.key});
  @override
  State<ParticipantListScreen> createState() => _ListState();
}

class _ListState extends State<ParticipantListScreen> {
  String q = '';
  @override
  Widget build(BuildContext context) => Loader<List>(
        load: (s) => s.run((a) async => await a.get('/participants') as List),
        builder: (c, all, reload) {
          final rows = [for (final p in all) if ('${p['id']} ${p['siteId']} ${p['statusDetail']}'.toLowerCase().contains(q.toLowerCase())) p];
          return SingleChildScrollView(
            padding: const EdgeInsets.all(K.s24),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              PageHeader(
                title: 'Participants',
                subtitle: '${all.length} pseudonymised participants in GBM-NL-2026-01',
                trailing: SizedBox(
                  width: 260,
                  child: TextField(onChanged: (v) => setState(() => q = v), decoration: const InputDecoration(hintText: 'Filter by ID, site, status', prefixIcon: Icon(Icons.search, size: 18))),
                ),
              ),
              const SizedBox(height: K.s16),
              Panel(
                padding: EdgeInsets.zero,
                child: rows.isEmpty
                    ? const SizedBox(height: 200, child: EmptyState(icon: Icons.search_off, title: 'No participants match', hint: 'Clear the filter to see all participants.'))
                    : Column(children: [
                        const TableHead([('Participant', 3, false), ('Site', 2, false), ('Status', 3, false), ('Age / sex', 2, false), ('eCRF verified', 3, false), ('AI pending', 2, true), ('Queries', 2, true)]),
                        for (final p in rows)
                          DataRow2(
                            key: ValueKey('p-${p['id']}'),
                            flex: const [3, 2, 3, 2, 3, 2, 2],
                            onTap: () => _go(context, '/participants/${p['id']}'),
                            cells: [
                              Text('${p['id']}', style: numStyle.copyWith(color: K.infoInk)),
                              Text('${p['siteId']}', style: K.small),
                              Align(alignment: Alignment.centerLeft, child: Pill('${p['statusDetail'] ?? p['status']}'.replaceAll('_', ' '), tone: statusTone('${p['status']}'))),
                              Text('${p['age']} · ${p['sex']}', style: K.small),
                              Row(children: [
                                SizedBox(width: 56, child: Bar((p['ecrfCompletePct'] as num) / 100, height: 5)),
                                const SizedBox(width: 8),
                                Text('${p['ecrfCompletePct']}%', style: K.mono),
                              ]),
                              Text('${p['extractionsPending']}', textAlign: TextAlign.right, style: numStyle),
                              Text('${p['openQueries']}', textAlign: TextAlign.right, style: numStyle),
                            ],
                          ),
                      ]),
              ),
            ]),
          );
        },
      );
}

class _W {
  final Map p, ecrf;
  final List docs;
  _W(this.p, this.ecrf, this.docs);
}

class ParticipantScreen extends StatelessWidget {
  final String id;
  const ParticipantScreen({super.key, required this.id});
  @override
  Widget build(BuildContext context) => Loader<_W>(
        load: (s) => s.run((a) async => _W(await a.get('/participants/$id') as Map, await a.get('/participants/$id/ecrf') as Map, await a.get('/participants/$id/documents') as List)),
        builder: (c, w, reload) => _Workspace(w, reload),
      );
}

class _Workspace extends StatefulWidget {
  final _W w;
  final VoidCallback reload;
  const _Workspace(this.w, this.reload);
  @override
  State<_Workspace> createState() => _WorkspaceState();
}

class _WorkspaceState extends State<_Workspace> {
  Map get p => widget.w.p;

  Future<void> _sdv(String field) async {
    final s = SessionScope.read(context);
    try {
      await s.api.post('/participants/${p['id']}/ecrf/$field/sdv');
      widget.reload();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('SDV failed: $e')));
    }
  }

  Future<void> _openDoc(String id) async {
    final s = SessionScope.read(context);
    final d = await s.run((a) async => await a.get('/documents/$id') as Map);
    if (!mounted) return;
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760, maxHeight: 640),
          child: Padding(
            padding: const EdgeInsets.all(K.s24),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Expanded(child: Text('${d['title']}', style: K.title)),
                IconButton(tooltip: 'Close', onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close)),
              ]),
              Text('${d['id']} · ${fmtDate(d['documentDate'])} · sha256 ${short('${d['sha256']}', 6)}', style: K.mono),
              const Divider(height: 24),
              Expanded(child: SingleChildScrollView(child: SelectableText('${d['text']}', style: const TextStyle(fontSize: 14.5, height: 1.65)))),
            ]),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final s = SessionScope.of(context);
    final ecrf = widget.w.ecrf, docs = widget.w.docs;
    final pending = p['extractionsPending'] as int;
    final visits = (p['visits'] as List?) ?? [];
    final treatments = (p['treatments'] as List?) ?? [];
    return SingleChildScrollView(
      padding: const EdgeInsets.all(K.s24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        PageHeader(
          crumbs: const [('Participants', '/participants'), ('Workspace', null)],
          title: '${p['id']}',
          subtitle: '${p['age']} y · ${p['sex']} · ${p['siteId']} · enrolled ${fmtDate(p['enrolledDate'])}',
          trailing: Row(mainAxisSize: MainAxisSize.min, children: [
            Pill('${p['statusDetail'] ?? p['status']}'.replaceAll('_', ' '), tone: statusTone('${p['status']}')),
            const SizedBox(width: 12),
            OutlinedButton.icon(
              key: const Key('open-timeline'),
              onPressed: () => _go(context, '/participants/${p['id']}/timeline'),
              icon: const Icon(Icons.timeline, size: 16),
              label: const Text('Timeline'),
            ),
            const SizedBox(width: 8),
            FilledButton.icon(
              onPressed: () => _go(context, '/review', p['id']),
              icon: const Icon(Icons.auto_awesome, size: 16),
              label: Text('Review AI ($pending)'),
            ),
          ]),
        ),
        if (p['summary'] != null) Padding(padding: const EdgeInsets.only(top: K.s12), child: Text('${p['summary']}', style: K.small.copyWith(fontSize: 13.5))),
        const SizedBox(height: K.s24),
        LayoutBuilder(builder: (c, box) {
          final main = Column(children: [_timeline(visits), const SizedBox(height: K.s16), _ecrf(ecrf, s), const SizedBox(height: K.s16), _treatments(treatments)]);
          final rail = Column(children: [_docs(docs), const SizedBox(height: K.s16), _quality(ecrf)]);
          return box.maxWidth >= 1000
              ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(flex: 8, child: main), const SizedBox(width: K.s16), Expanded(flex: 4, child: rail)])
              : Column(children: [main, const SizedBox(height: K.s16), rail]);
        }),
      ]),
    );
  }

  Widget _timeline(List visits) => Panel(
        title: 'Visit timeline',
        child: visits.isEmpty
            ? const Text('No visits recorded.', style: K.small)
            : Column(children: [
                for (var i = 0; i < visits.length; i++)
                  IntrinsicHeight(
                    child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                      SizedBox(
                        width: 20,
                        child: Column(children: [
                          Container(
                            width: 10, height: 10, margin: const EdgeInsets.only(top: 5),
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: visits[i]['status'] == 'completed' ? K.ink2 : K.surface,
                              border: Border.all(color: visits[i]['status'] == 'completed' ? K.ink2 : K.accent, width: 2),
                            ),
                          ),
                          if (i < visits.length - 1) Expanded(child: Container(width: 1, color: K.lineStrong)),
                        ]),
                      ),
                      Expanded(
                        child: Padding(
                          padding: const EdgeInsets.only(bottom: 10, left: 4),
                          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Expanded(
                              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                Text('${visits[i]['name']}', style: K.body.copyWith(fontWeight: FontWeight.w500)),
                                if ('${visits[i]['note'] ?? ''}'.isNotEmpty) Text('${visits[i]['note']}', style: K.small),
                              ]),
                            ),
                            Text(fmtDate(visits[i]['date']), style: K.mono),
                            const SizedBox(width: 12),
                            SizedBox(width: 96, child: Align(alignment: Alignment.centerRight, child: Pill('${visits[i]['status']}'.replaceAll('_', ' '), tone: statusTone('${visits[i]['status']}')))),
                          ]),
                        ),
                      ),
                    ]),
                  ),
              ]),
      );

  Widget _ecrf(Map ecrf, Session s) {
    final fields = (ecrf['fields'] as List).cast<Map>();
    return Panel(
      title: 'eCRF · ${ecrf['formId']}',
      trailing: Text('${ecrf['verified']}/${ecrf['total']} verified', style: K.mono),
      padding: EdgeInsets.zero,
      child: fields.isEmpty
          ? const Padding(padding: EdgeInsets.all(K.s16), child: Text('eCRF is not part of the offline snapshot.', style: K.small))
          : Column(children: [
              const TableHead([('Field', 4, false), ('Value', 4, false), ('State', 3, false), ('', 2, true)]),
              for (final f in fields)
                DataRow2(
                  flex: const [4, 4, 3, 2],
                  cells: [
                    Text('${f['label']}${f['required'] == true ? ' *' : ''}', style: K.body.copyWith(fontSize: 13), overflow: TextOverflow.ellipsis),
                    Text(f['value'] == null ? '—' : '${f['value']['value']}${f['unit'] != null ? ' ${f['unit']}' : ''}', style: numStyle.copyWith(fontWeight: FontWeight.w400), overflow: TextOverflow.ellipsis),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: f['value'] != null
                          ? (f['value']['sdvAt'] != null
                              ? const Pill('SDV done', tone: Tone.ok, icon: Icons.verified_user_outlined)
                              : const Pill('Verified', tone: Tone.ok, icon: Icons.check_circle_outline))
                          : f['pendingExtractionId'] != null
                              ? const Pill('AI · Unverified', tone: Tone.ai, icon: Icons.auto_awesome)
                              : const Pill('Empty', tone: Tone.muted),
                    ),
                    f['value'] != null && f['value']['sdvAt'] == null
                        ? Align(
                            alignment: Alignment.centerRight,
                            child: WriteGate(
                              blockedReason: s.offline ? s.writeBlockedReason : s.role != 'monitor' ? 'Source data verification is a monitor action.' : null,
                              builder: (en) => TextButton(onPressed: en ? () => _sdv('${f['id']}') : null, child: const Text('Mark SDV')),
                            ),
                          )
                        : const SizedBox(),
                  ],
                ),
            ]),
    );
  }

  Widget _treatments(List t) => Panel(
        title: 'Treatment history',
        padding: EdgeInsets.zero,
        child: t.isEmpty
            ? const Padding(padding: EdgeInsets.all(K.s16), child: Text('No treatment recorded.', style: K.small))
            : Column(children: [
                for (final x in t)
                  DataRow2(
                    flex: const [5, 4, 3],
                    cells: [
                      Text('${x['name']}', style: K.body.copyWith(fontSize: 13, fontWeight: FontWeight.w500)),
                      Text('${x['dose'] ?? ''}', style: K.small),
                      Text('${fmtDate(x['start'])} → ${x['end'] == null ? 'ongoing' : fmtDate(x['end'])}', style: K.mono.copyWith(fontSize: 11.5)),
                    ],
                  ),
              ]),
      );

  Widget _docs(List docs) => Panel(
        title: 'Source documents · ${docs.length}',
        padding: EdgeInsets.zero,
        child: Column(children: [
          for (final d in docs)
            DataRow2(
              key: ValueKey('doc-${d['id']}'),
              flex: const [1],
              onTap: () => _openDoc('${d['id']}'),
              height: 56,
              cells: [
                Row(children: [
                  const Icon(Icons.description_outlined, size: 18, color: K.ink2),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
                      Text('${d['title']}', style: K.body.copyWith(fontSize: 13, fontWeight: FontWeight.w500), maxLines: 1, overflow: TextOverflow.ellipsis),
                      Text('${d['id']} · ${fmtDate(d['documentDate'])} · ${d['extractionCount'] ?? 0} AI values', style: K.small.copyWith(fontSize: 11.5)),
                    ]),
                  ),
                ]),
              ],
            ),
        ]),
      );

  Widget _quality(Map ecrf) {
    final queries = p['openQueries'] as int;
    final pend = p['extractionsPending'] as int;
    return Panel(
      title: 'Data quality',
      child: Column(children: [
        _qrow(Icons.help_outline, 'Open queries', '$queries'),
        _qrow(Icons.auto_awesome, 'AI proposals awaiting review', '$pend'),
        _qrow(Icons.check_circle_outline, 'eCRF fields verified', '${ecrf['verified']}/${ecrf['total']}'),
      ]),
    );
  }

  Widget _qrow(IconData i, String l, String v) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(children: [Icon(i, size: 16, color: K.ink2), const SizedBox(width: 8), Expanded(child: Text(l, style: K.body.copyWith(fontSize: 13))), Text(v, style: numStyle)]),
      );
}
