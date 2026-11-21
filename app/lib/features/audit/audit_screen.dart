import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../data/app_state.dart';
import '../../models/models.dart';
import '../../theme/tokens.dart';
import '../../ui/widgets.dart';

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
          padding: const EdgeInsets.fromLTRB(K.s32, 28, K.s32, K.s24),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            PageHeader(
              title: 'Audit trail',
              subtitle: 'Append-only record of every AI proposal and human decision.',
              trailing: Pill('${rows.length} ${rows.length == 1 ? 'event' : 'events'}', tone: Tone.muted),
            ),
            const SizedBox(height: K.s16),
            Wrap(spacing: 12, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
              SegmentedButton<EventSource?>(
                showSelectedIcon: false,
                style: SegmentedButton.styleFrom(
                  backgroundColor: K.surface,
                  selectedBackgroundColor: K.accentSoft,
                  selectedForegroundColor: K.accent,
                  foregroundColor: K.ink2,
                  side: const BorderSide(color: K.lineStrong),
                  textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                ),
                segments: const [
                  ButtonSegment(value: null, label: Text('All')),
                  ButtonSegment(value: EventSource.ai, label: Text('AI'), icon: Icon(Icons.auto_awesome, size: 16)),
                  ButtonSegment(value: EventSource.human, label: Text('Human'), icon: Icon(Icons.person_outline, size: 16)),
                ],
                selected: {src},
                onSelectionChanged: (s) => setState(() => src = s.first),
              ),
              Container(
                height: 40,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(color: K.surface, border: Border.all(color: K.lineStrong), borderRadius: BorderRadius.circular(8)),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: action,
                    borderRadius: BorderRadius.circular(10),
                    style: K.body.copyWith(fontWeight: FontWeight.w500),
                    items: [for (final a in _actions) DropdownMenuItem(value: a, child: Text(a == 'all' ? 'All actions' : a[0].toUpperCase() + a.substring(1)))],
                    onChanged: (v) => setState(() => action = v!),
                  ),
                ),
              ),
              SizedBox(
                width: 300,
                child: TextField(
                  style: K.body,
                  decoration: InputDecoration(hintText: 'Search actor, participant, field', hintStyle: K.body.copyWith(color: K.ink3), prefixIcon: const Icon(Icons.search, size: 18)),
                  onChanged: (v) => setState(() => q = v),
                ),
              ),
            ]),
            const SizedBox(height: K.s16),
            Expanded(
              child: rows.isEmpty
                  ? Panel(
                      child: SizedBox(
                        height: 260,
                        child: all.isEmpty
                            ? EmptyState(
                                icon: Icons.history,
                                title: 'No audit events yet',
                                hint: 'Open AI review, then accept, correct, reject or defer a value. Each decision is recorded here.',
                                action: FilledButton(onPressed: () => Navigator.of(context).pushReplacementNamed('/review'), child: const Text('Open AI review')),
                              )
                            : EmptyState(
                                icon: Icons.filter_alt_off_outlined,
                                title: 'No events match these filters',
                                hint: 'Clear the search or choose another source or action.',
                                action: OutlinedButton(onPressed: () => setState(() { src = null; action = 'all'; q = ''; }), child: const Text('Clear filters')),
                              ),
                      ),
                    )
                  : Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                      Expanded(flex: 896, child: _tableBox(rows)),
                      if (sel != null) ...[const SizedBox(width: K.s16), Expanded(flex: 400, child: _detail(sel!, all))],
                    ]),
            ),
          ]),
        );
      },
    );
  }

  Widget _tableBox(List<AuditEvent> rows) => DecoratedBox(
        decoration: BoxDecoration(color: K.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: K.line)),
        child: Column(children: [
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: K.s16, vertical: 12),
            child: Row(children: [
              SizedBox(width: 72, child: Text('TIME', style: K.label)),
              SizedBox(width: 108, child: Text('SOURCE', style: K.label)),
              SizedBox(width: 76, child: Text('ACTION', style: K.label)),
              Expanded(flex: 4, child: Text('PARTICIPANT · FIELD', style: K.label)),
              Expanded(flex: 4, child: Text('CHANGE', style: K.label)),
            ]),
          ),
          const Divider(),
          Expanded(child: _table(rows)),
        ]),
      );

  Widget _table(List<AuditEvent> rows) => ListView.separated(
        itemCount: rows.length,
        separatorBuilder: (_, _) => const Divider(),
        itemBuilder: (_, k) {
          final e = rows[k];
          final ai = e.source == EventSource.ai;
          final selected = e == sel;
          return InkWell(
            key: ValueKey('audit-row-$k'),
            onTap: () => setState(() => sel = e),
            child: AnimatedContainer(
              duration: K.fast,
              color: selected ? K.accentSoft : Colors.transparent,
              padding: const EdgeInsets.symmetric(horizontal: K.s16, vertical: 12),
              child: Row(children: [
                SizedBox(width: 72, child: Text(_t(e.timestamp), style: K.mono)),
                SizedBox(width: 108, child: Align(alignment: Alignment.centerLeft, child: _badge(ai))),
                SizedBox(width: 76, child: Text(e.action, style: K.body.copyWith(fontWeight: FontWeight.w600, fontSize: 13))),
                Expanded(flex: 4, child: Text(e.field, style: K.body.copyWith(fontSize: 13), overflow: TextOverflow.ellipsis)),
                Expanded(
                  flex: 4,
                  child: Text(
                    e.before != null || e.after != null ? '${e.before ?? '—'} → ${e.after ?? '—'}' : '',
                    style: K.mono,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ]),
            ),
          );
        },
      );

  Widget _badge(bool ai) => Pill(ai ? 'AI' : 'Human', tone: ai ? Tone.ai : Tone.ok, icon: ai ? Icons.auto_awesome : Icons.person_outline);

  String _t(DateTime d) => d.toIso8601String().substring(11, 19);

  Widget _detail(AuditEvent e, List<AuditEvent> all) {
    Widget row(String k, String? v) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 5),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            SizedBox(width: 82, child: Text(k, style: K.small)),
            Expanded(child: SelectableText(v ?? '—', style: K.body.copyWith(fontSize: 13))),
          ]),
        );
    final json = jsonEncode({
      'actor': e.actor, 'action': e.action, 'field': e.field, 'before': e.before, 'after': e.after,
      'source': e.source.name, 'model': e.model, 'promptVersion': e.promptVersion, 'timestamp': e.timestamp.toIso8601String(),
    });
    return FadeIn(
      key: ValueKey(e),
      child: DecoratedBox(
        decoration: BoxDecoration(color: K.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: K.line)),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(K.s16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(child: Text('Event #${(all.length - all.indexOf(e)).toString().padLeft(4, '0')}', style: K.heading)),
              IconButton(tooltip: 'Close', icon: const Icon(Icons.close, size: 18), onPressed: () => setState(() => sel = null)),
            ]),
            const SizedBox(height: 4),
            _badge(e.source == EventSource.ai),
            const SizedBox(height: K.s12),
            row('Time', e.timestamp.toIso8601String()),
            row('Actor', e.actor),
            row('Verification', e.source == EventSource.ai ? 'AI · unverified' : 'Human · verified'),
            row('Action', e.action),
            row('Field', e.field),
            row('Before', e.before),
            row('After', e.after),
            row('Model', e.model),
            row('Prompt', e.promptVersion),
            const SizedBox(height: K.s12),
            const Text('Append-only demo audit store; no edit or delete controls.', style: K.small),
            const SizedBox(height: K.s12),
            OutlinedButton.icon(
              icon: const Icon(Icons.copy, size: 16),
              label: const Text('Copy event JSON'),
              onPressed: () async {
                await Clipboard.setData(ClipboardData(text: json));
                if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Event JSON copied')));
              },
            ),
          ]),
        ),
      ),
    );
  }
}
