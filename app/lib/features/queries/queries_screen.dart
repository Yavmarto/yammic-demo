import 'package:flutter/material.dart';
import '../../data/session.dart';
import '../../theme/tokens.dart';
import '../../ui/async.dart';
import '../../ui/format.dart';
import '../../ui/widgets.dart';

/// Queries inbox, role-aware: the monitor opens queries, the nurse/PI resolves them.
class QueriesScreen extends StatefulWidget {
  const QueriesScreen({super.key});
  @override
  State<QueriesScreen> createState() => _QueriesScreenState();
}

class _QueriesScreenState extends State<QueriesScreen> {
  String filter = 'open';
  String? openId;
  int rev = 0;

  void _snack(String m) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(m)));

  Future<void> _close(Session s, Map q, VoidCallback reload) async {
    try {
      await s.api.post('/queries/${q['id']}/close');
      reload();
    } catch (e) {
      if (mounted) _snack('Could not close the query: $e');
    }
  }

  Future<void> _answer(Session s, Map q, String text, VoidCallback reload) async {
    try {
      await s.api.post('/queries/${q['id']}/answer', {'answer': text});
      reload();
    } catch (e) {
      if (mounted) _snack('Could not close the query: $e');
    }
  }

  Future<void> _ask(Session s) async {
    final pid = TextEditingController(), field = TextEditingController(), text = TextEditingController();
    var sev = 'medium';
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => StatefulBuilder(
        builder: (c, set) => AlertDialog(
          title: const Text('Ask a query'),
          content: SizedBox(
            width: 420,
            child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
              TextField(key: const Key('q-participant'), controller: pid, decoration: const InputDecoration(labelText: 'Participant ID', hintText: 'GBM-NL-001')),
              const SizedBox(height: K.s8),
              TextField(key: const Key('q-field'), controller: field, decoration: const InputDecoration(labelText: 'Field (optional)', hintText: 'KPS')),
              const SizedBox(height: K.s8),
              TextField(key: const Key('q-text'), controller: text, maxLines: 3, decoration: const InputDecoration(labelText: 'Question for the site')),
              const SizedBox(height: K.s12),
              SegmentedButton<String>(
                segments: const [ButtonSegment(value: 'low', label: Text('Low')), ButtonSegment(value: 'medium', label: Text('Medium')), ButtonSegment(value: 'high', label: Text('High'))],
                selected: {sev},
                onSelectionChanged: (v) => set(() => sev = v.first),
              ),
            ]),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Cancel')),
            FilledButton(key: const Key('q-send'), onPressed: () => Navigator.pop(c, true), child: const Text('Send query')),
          ],
        ),
      ),
    );
    if (ok != true || pid.text.trim().isEmpty || text.text.trim().isEmpty) return;
    try {
      await s.api.post('/queries', {'participantId': pid.text.trim(), 'text': text.text.trim(), 'severity': sev, if (field.text.trim().isNotEmpty) 'fieldId': field.text.trim()});
      setState(() => rev++);
    } catch (e) {
      if (mounted) _snack('Could not send the query: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = SessionScope.of(context);
    return Loader<List>(
      key: ValueKey('$filter-$rev'),
      load: (s) => s.run((a) async => await a.get('/queries', query: filter == 'all' ? null : {'status': filter}) as List),
      builder: (context, items, reload) => ListView(padding: const EdgeInsets.all(K.s24), children: [
        PageHeader(
          title: 'Queries',
          subtitle: s.isMonitor ? 'Questions you asked the sites. Ask a new one from here or from a participant field.' : 'Questions from the monitor. Answer in the source, then resolve.',
          trailing: s.isMonitor && !s.offline ? FilledButton.icon(key: const Key('ask-query'), onPressed: () => _ask(s), icon: const Icon(Icons.add, size: 18), label: const Text('Ask a query')) : null,
        ),
        const SizedBox(height: K.s16),
        Wrap(spacing: 8, children: [
          for (final f in const [('open', 'Open'), ('answered', 'Answered'), ('closed', 'Closed'), ('all', 'All')])
            ChoiceChip(key: Key('qf-${f.$1}'), label: Text(f.$2), selected: filter == f.$1, onSelected: (_) => setState(() => filter = f.$1)),
        ]),
        const SizedBox(height: K.s16),
        if (items.isEmpty)
          const Panel(child: EmptyState(icon: Icons.help_outline, title: 'No queries here', hint: 'Open queries from the monitor appear in this inbox.'))
        else
          Panel(padding: EdgeInsets.zero, child: Column(children: [
            const TableHead([('Participant', 2, false), ('Field', 2, false), ('Question', 6, false), ('Site', 2, false), ('Status', 2, false)]),
            for (final q in items.cast<Map>()) ...[
              DataRow2(
                key: Key('q-${q['id']}'),
                flex: const [2, 2, 6, 2, 2],
                onTap: () => setState(() => openId = openId == '${q['id']}' ? null : '${q['id']}'),
                selected: openId == '${q['id']}',
                cells: [
                  Text('${q['participantId']}', style: K.mono),
                  Text(q['fieldId'] == null ? '—' : '${q['fieldId']}', style: K.small),
                  Text('${q['text']}', maxLines: 2, overflow: TextOverflow.ellipsis, style: K.body),
                  Text('${q['siteId']}', style: K.small),
                  Align(alignment: Alignment.centerLeft, child: switch ('${q['status']}') {
                    'open' => Pill('Open', tone: q['severity'] == 'high' ? Tone.bad : Tone.ai, icon: Icons.help_outline),
                    'answered' => const Pill('Answered', tone: Tone.info, icon: Icons.reply),
                    _ => const Pill('Closed', tone: Tone.ok, icon: Icons.check),
                  }),
                ],
              ),
              if (openId == '${q['id']}') _Thread(q: q, s: s, onClose: () => _close(s, q, reload), onAnswer: (t) => _answer(s, q, t, reload)),
            ],
          ])),
      ]),
    );
  }
}

class _Thread extends StatefulWidget {
  final Map q;
  final Session s;
  final VoidCallback onClose;
  final ValueChanged<String> onAnswer;
  const _Thread({required this.q, required this.s, required this.onClose, required this.onAnswer});
  @override
  State<_Thread> createState() => _ThreadState();
}

class _ThreadState extends State<_Thread> {
  final reply = TextEditingController();
  @override
  void dispose() {
    reply.dispose();
    super.dispose();
  }

  Widget _msg(String who, Object? when, String text, {bool closed = false}) => Padding(
        padding: const EdgeInsets.only(bottom: K.s8),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(closed ? Icons.check_circle_outline : Icons.chat_bubble_outline, size: 16, color: closed ? K.okLine : K.ink3),
          const SizedBox(width: 8),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('$who · ${fmtDateTime(when)}', style: K.small),
            Text(text, style: K.body),
          ])),
        ]),
      );

  @override
  Widget build(BuildContext context) {
    final q = widget.q, s = widget.s;
    final st = '${q['status']}';
    final live = !s.offline;
    final canAnswer = live && st == 'open' && (s.role == 'nurse' || s.isPi);
    final canClose = live && st != 'closed' && (s.isMonitor || s.isPi || (s.role == 'nurse' && st == 'answered'));
    return Container(
      key: Key('thread-${q['id']}'),
      padding: const EdgeInsets.fromLTRB(K.s24, K.s12, K.s16, K.s12),
      color: K.sidebar,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _msg('${q['openedBy']} (query)', q['createdAt'], '${q['text']}'),
        if (q['answer'] != null) _msg('${q['answeredBy']} (answer)', q['answeredAt'], '${q['answer']}'),
        if (st == 'closed') _msg('${q['closedBy']} (closed)', q['closedAt'], 'Query closed.', closed: true),
        if (canAnswer)
          Padding(
            padding: const EdgeInsets.only(bottom: K.s8),
            child: Row(children: [
              Expanded(child: TextField(key: const Key('answer-text'), controller: reply, decoration: const InputDecoration(hintText: 'Answer from the source record'))),
              const SizedBox(width: 8),
              FilledButton(key: Key('answer-${q['id']}'), onPressed: () => reply.text.trim().isEmpty ? null : widget.onAnswer(reply.text.trim()), child: const Text('Send answer')),
            ]),
          ),
        Row(children: [
          TextButton.icon(onPressed: () => Navigator.of(context).pushNamed('/participants/${q['participantId']}'), icon: const Icon(Icons.open_in_new, size: 16), label: const Text('Open participant')),
          const Spacer(),
          if (st == 'open' && s.isMonitor) Text('Waiting for the site to answer', style: K.small),
          if (canClose) FilledButton(key: Key('close-${q['id']}'), onPressed: widget.onClose, child: Text(s.isMonitor ? 'Close query' : 'Resolve query')),
        ]),
      ]),
    );
  }
}
