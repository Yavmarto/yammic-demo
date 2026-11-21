import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../data/session.dart';
import '../../theme/tokens.dart';
import '../../ui/format.dart';
import '../../ui/widgets.dart';

class AuditScreen extends StatefulWidget {
  const AuditScreen({super.key});
  @override
  State<AuditScreen> createState() => _AuditState();
}

class _AuditState extends State<AuditScreen> {
  String source = 'all', participant = '';
  bool hideSignIns = true; // sign-ins bury the AI/human story; one tap shows them
  final actionCtl = TextEditingController();
  final partCtl = TextEditingController();
  Map? page;
  Map? verify;
  bool verifying = false, loading = true;
  Object? error;
  Map? selected;
  Session? s;
  bool _init = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    s = SessionScope.read(context);
    if (!_init) {
      _init = true;
      final arg = ModalRoute.of(context)?.settings.arguments;
      if (arg is String) { participant = arg; partCtl.text = arg; }
      _load();
    }
  }

  Future<void> _load() async {
    setState(() { loading = true; error = null; });
    try {
      final q = {
        'limit': '200',
        if (source != 'all') 'source': source,
        if (participant.isNotEmpty) 'participant_id': participant,
        if (actionCtl.text.trim().isNotEmpty) 'action': '${actionCtl.text.trim()}*',
      };
      final r = await s!.run((a) async => await a.get('/audit', query: q) as Map);
      if (mounted) setState(() { page = r; loading = false; selected = null; });
    } catch (e) {
      if (mounted) setState(() { error = e; loading = false; });
    }
  }

  Future<void> _verify() async {
    setState(() => verifying = true);
    try {
      final r = await s!.run((a) async => await a.get('/audit/verify') as Map);
      if (mounted) setState(() => verify = r);
    } catch (e) {
      if (mounted) setState(() => verify = {'ok': false, 'count': 0, 'reason': '$e'});
    }
    if (mounted) setState(() => verifying = false);
  }

  @override
  Widget build(BuildContext context) {
    final all = (page?['items'] as List?) ?? [];
    final items = hideSignIns ? all.where((e) => e['action'] != 'auth.login').toList() : all;
    return Padding(
      padding: const EdgeInsets.all(K.s24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        PageHeader(
          title: 'Audit trail',
          subtitle: 'Append-only, hash-chained. Every AI proposal and human decision is recorded.',
          trailing: FilledButton.icon(
            onPressed: verifying ? null : _verify,
            icon: verifying ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.verified_user_outlined, size: 18),
            label: Text(verifying ? 'Verifying…' : 'Verify chain'),
          ),
        ),
        if (verify != null) _verifyBanner(),
        const SizedBox(height: K.s16),
        _filters(items),
        const SizedBox(height: K.s12),
        Expanded(
          child: loading
              ? const Panel(child: SizedBox(height: 200, child: Center(child: CircularProgressIndicator())))
              : error != null
                  ? ErrorState(message: '$error', onRetry: _load)
                  : items.isEmpty
                      ? Panel(child: SizedBox(height: 200, child: EmptyState(icon: Icons.history, title: s!.offline ? 'Audit trail needs the live backend' : 'No events match', hint: s!.offline ? 'The offline snapshot has no audit data. Retry the connection.' : 'Clear a filter to widen the search.')))
                      : Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                          Expanded(child: _table(items)),
                          if (selected != null) ...[const SizedBox(width: K.s16), SizedBox(width: 380, child: _detail(selected!))],
                        ]),
        ),
      ]),
    );
  }

  Widget _verifyBanner() {
    final ok = verify!['ok'] == true;
    return Container(
      margin: const EdgeInsets.only(top: K.s12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: ok ? K.tealBg : K.badBg, borderRadius: BorderRadius.circular(10), border: Border.all(color: ok ? K.teal : K.badLine)),
      child: Row(children: [
        Icon(ok ? Icons.verified_user : Icons.gpp_bad_outlined, color: ok ? K.tealInk : K.badInk, size: 20),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            ok
                ? 'Chain verified · ${verify!['count']} events, no gaps or edits. Head ${short('${verify!['headHash']}', 6)}'
                : 'Chain broken at event #${verify!['brokenSeq']}: ${verify!['reason']}',
            key: const ValueKey('verify-result'),
            style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w500, color: ok ? K.tealInk : K.badInk),
          ),
        ),
      ]),
    );
  }

  Widget _filters(List items) => Wrap(spacing: 12, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
        SegmentedButton<String>(
          showSelectedIcon: false,
          style: SegmentedButton.styleFrom(visualDensity: VisualDensity.compact),
          segments: const [ButtonSegment(value: 'all', label: Text('All')), ButtonSegment(value: 'ai', label: Text('AI')), ButtonSegment(value: 'human', label: Text('Human'))],
          selected: {source},
          onSelectionChanged: (v) { source = v.first; _load(); },
        ),
        SizedBox(width: 260, child: TextField(controller: actionCtl, onSubmitted: (_) => _load(), decoration: const InputDecoration(hintText: 'Action prefix (e.g. extraction)', prefixIcon: Icon(Icons.filter_alt_outlined, size: 18)))),
        SizedBox(
          width: 200,
          child: TextField(
            controller: partCtl,
            onSubmitted: (v) { participant = v.trim(); _load(); },
            decoration: const InputDecoration(hintText: 'Participant ID', prefixIcon: Icon(Icons.person_search_outlined, size: 18)),
          ),
        ),
        FilterChip(label: const Text('Hide sign-ins'), selected: hideSignIns, onSelected: (v) => setState(() { hideSignIns = v; selected = null; })),
        if (page != null) Text('${items.length} shown · ${page!['total']} in chain', style: K.small),
      ]);

  Widget _table(List items) => Panel(
        fill: true,
        padding: EdgeInsets.zero,
        child: Column(children: [
          const TableHead([('Seq', 1, false), ('Time', 3, false), ('Actor', 3, false), ('Action', 4, false), ('Entity', 4, false), ('', 1, true)]),
          Expanded(
            child: ListView.builder(
              itemCount: items.length,
              itemBuilder: (_, k) {
                final e = items[k] as Map;
                return DataRow2(
                  key: ValueKey('audit-${e['seq']}'),
                  height: 40,
                  selected: identical(selected, e),
                  flex: const [1, 3, 3, 4, 4, 1],
                  onTap: () => setState(() => selected = e),
                  cells: [
                    Text('${e['seq']}', style: K.mono),
                    Text(fmtDateTime(e['ts']), style: K.mono.copyWith(fontSize: 11.5)),
                    Text('${e['actor']}', style: K.small.copyWith(color: K.ink), overflow: TextOverflow.ellipsis),
                    Text('${e['action']}', style: K.body.copyWith(fontSize: 13, fontWeight: FontWeight.w500), overflow: TextOverflow.ellipsis),
                    Text('${e['entityType']} · ${e['entityId']}', style: K.small, overflow: TextOverflow.ellipsis),
                    Align(alignment: Alignment.centerRight, child: Tooltip(message: e['source'] == 'ai' ? 'AI-originated' : 'Human action', child: Icon(e['source'] == 'ai' ? Icons.auto_awesome : Icons.person_outline, size: 15, color: e['source'] == 'ai' ? K.aiInk : K.ink2))),
                  ],
                );
              },
            ),
          ),
        ]),
      );

  Widget _detail(Map e) {
    const enc = JsonEncoder.withIndent('  ');
    Widget kv(String k, String v) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [SizedBox(width: 84, child: Text(k, style: K.small)), Expanded(child: SelectableText(v, style: K.mono.copyWith(color: K.ink)))]),
        );
    Widget block(String t, Object? v) => v == null
        ? const SizedBox()
        : Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(t, style: K.label),
              const SizedBox(height: 4),
              Container(width: double.infinity, padding: const EdgeInsets.all(10), decoration: BoxDecoration(color: K.bg, borderRadius: BorderRadius.circular(8), border: Border.all(color: K.line)), child: SelectableText(enc.convert(v), style: K.mono.copyWith(color: K.ink))),
            ]),
          );
    return Panel(
      title: 'Event #${e['seq']}',
      fill: true,
      trailing: IconButton(tooltip: 'Close', onPressed: () => setState(() => selected = null), icon: const Icon(Icons.close, size: 18)),
      child: SingleChildScrollView(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Pill(e['source'] == 'ai' ? 'AI · ${e['model'] ?? ''}' : 'Human · ${e['role']}', tone: e['source'] == 'ai' ? Tone.ai : Tone.muted, icon: e['source'] == 'ai' ? Icons.auto_awesome : Icons.person_outline),
          const SizedBox(height: 8),
          kv('Time', fmtDateTime(e['ts'])),
          kv('Actor', '${e['actor']}'),
          kv('Action', '${e['action']}'),
          kv('Entity', '${e['entityType']} ${e['entityId']}'),
          if (e['participantId'] != null) kv('Participant', '${e['participantId']}'),
          if (e['promptVersion'] != null) kv('Prompt', '${e['promptVersion']}'),
          block('BEFORE', e['before']),
          block('AFTER', e['after']),
          const SizedBox(height: 12),
          kv('Prev hash', short('${e['prevHash']}', 10)),
          Row(children: [
            Expanded(child: kv('Hash', short('${e['hash']}', 10))),
            IconButton(tooltip: 'Copy hash', icon: const Icon(Icons.copy, size: 16), onPressed: () => Clipboard.setData(ClipboardData(text: '${e['hash']}'))),
          ]),
        ]),
      ),
    );
  }
}
