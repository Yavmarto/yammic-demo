import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../data/app_state.dart';
import '../../models/models.dart';

/// Read-only audit list. Participant is encoded in `field` as "participant · label" by the review screen.
class AuditScreen extends StatefulWidget {
  const AuditScreen({super.key});
  @override
  State<AuditScreen> createState() => _AuditScreenState();
}

class _AuditScreenState extends State<AuditScreen> {
  EventSource? src;
  String action = 'all', q = '';
  AuditEvent? sel;

  static const _actions = ['all', 'extract', 'accept', 'correct', 'reject', 'defer'];

  @override
  Widget build(BuildContext context) {
    final audit = AppScope.of(context).audit;
    return ListenableBuilder(
      listenable: audit,
      builder: (context, _) {
        final all = audit.events.reversed.toList();
        final rows = [
          for (final e in all)
            if ((src == null || e.source == src) &&
                (action == 'all' || e.action == action) &&
                (q.isEmpty || '${e.actor} ${e.field}'.toLowerCase().contains(q.toLowerCase())))
              e
        ];
        if (sel != null && !rows.contains(sel)) sel = null;
        return Padding(
          padding: const EdgeInsets.all(20),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Text('Audit trail', style: Theme.of(context).textTheme.titleLarge),
              const Spacer(),
              SegmentedButton<EventSource?>(
                showSelectedIcon: false,
                segments: const [
                  ButtonSegment(value: null, label: Text('All')),
                  ButtonSegment(value: EventSource.ai, label: Text('AI'), icon: Icon(Icons.auto_awesome)),
                  ButtonSegment(value: EventSource.human, label: Text('Human'), icon: Icon(Icons.person_outline)),
                ],
                selected: {src},
                onSelectionChanged: (s) => setState(() => src = s.first),
              ),
              const SizedBox(width: 12),
              DropdownButton<String>(
                value: action,
                items: [for (final a in _actions) DropdownMenuItem(value: a, child: Text(a == 'all' ? 'All actions' : a))],
                onChanged: (v) => setState(() => action = v!),
              ),
              const SizedBox(width: 12),
              SizedBox(
                width: 220,
                child: TextField(
                  decoration: const InputDecoration(hintText: 'Search actor, participant, field', prefixIcon: Icon(Icons.search), isDense: true, border: OutlineInputBorder()),
                  onChanged: (v) => setState(() => q = v),
                ),
              ),
            ]),
            const SizedBox(height: 8),
            Text('${rows.length} events'),
            const SizedBox(height: 8),
            Expanded(
              child: rows.isEmpty
                  ? Center(child: Text(all.isEmpty
                      ? 'No audit events yet. Open AI review and accept, correct, reject or defer a value.'
                      : 'No events match these filters.'))
                  : Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                      Expanded(flex: 896, child: Card(child: _table(rows))),
                      if (sel != null) ...[const SizedBox(width: 16), Expanded(flex: 400, child: Card(child: _detail(sel!, all)))],
                    ]),
            ),
          ]),
        );
      },
    );
  }

  Widget _table(List<AuditEvent> rows) => ListView.separated(
        itemCount: rows.length,
        separatorBuilder: (_, _) => const Divider(),
        itemBuilder: (_, k) {
          final e = rows[k];
          final ai = e.source == EventSource.ai;
          return ListTile(
            key: ValueKey('audit-row-$k'),
            dense: true,
            selected: e == sel,
            selectedTileColor: const Color(0xFFD7E3F7),
            onTap: () => setState(() => sel = e),
            leading: _badge(ai),
            title: Text('${e.action} · ${e.field}', overflow: TextOverflow.ellipsis),
            subtitle: Text('${_t(e.timestamp)} · ${e.actor}${e.before != null || e.after != null ? ' · ${e.before ?? '—'} → ${e.after ?? '—'}' : ''}',
                style: const TextStyle(fontFamily: 'monospace'), overflow: TextOverflow.ellipsis),
          );
        },
      );

  Widget _badge(bool ai) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: ai ? const Color(0xFFFFF1CC) : const Color(0xFFE4F3E9),
          border: Border.all(color: ai ? const Color(0xFF8A5A00) : const Color(0xFF1E6B42)),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(ai ? Icons.auto_awesome : Icons.person_outline, size: 16),
          const SizedBox(width: 4),
          Text(ai ? 'AI' : 'Human', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
        ]),
      );

  String _t(DateTime d) => d.toIso8601String().substring(11, 19);

  Widget _detail(AuditEvent e, List<AuditEvent> all) {
    Widget row(String k, String? v) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 3),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            SizedBox(width: 90, child: Text(k, style: const TextStyle(fontWeight: FontWeight.w600))),
            Expanded(child: SelectableText(v ?? '—')),
          ]),
        );
    final json = jsonEncode({
      'actor': e.actor, 'action': e.action, 'field': e.field, 'before': e.before, 'after': e.after,
      'source': e.source.name, 'model': e.model, 'promptVersion': e.promptVersion, 'timestamp': e.timestamp.toIso8601String(),
    });
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Event #${(all.length - all.indexOf(e)).toString().padLeft(4, '0')}', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        row('Time', e.timestamp.toIso8601String()),
        row('Actor', e.actor),
        row('Source', e.source == EventSource.ai ? 'AI · unverified' : 'Human · verified'),
        row('Action', e.action),
        row('Field', e.field),
        row('Before', e.before),
        row('After', e.after),
        row('Model', e.model),
        row('Prompt', e.promptVersion),
        const SizedBox(height: 8),
        const Text('Append-only demo audit store; no edit or delete controls.', style: TextStyle(fontSize: 12)),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          icon: const Icon(Icons.copy),
          label: const Text('Copy event JSON'),
          onPressed: () async {
            await Clipboard.setData(ClipboardData(text: json));
            if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Event JSON copied')));
          },
        ),
      ]),
    );
  }
}
