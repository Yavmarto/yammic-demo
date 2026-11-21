import 'package:flutter/material.dart';
import '../../data/session.dart';
import '../../theme/tokens.dart';
import '../../ui/async.dart';
import '../../ui/format.dart';
import '../../ui/v4_widgets.dart';
import '../../ui/widgets.dart';

const _filters = [('screening', 'To screen'), ('eligible', 'Eligible'), ('screen_fail', 'Screen-fail'), ('all', 'All')];

(String, Tone, IconData) statusLook(String s) => switch (s) {
      'screening' => ('Screening', Tone.info, Icons.pending_outlined),
      'eligible' => ('Eligible', Tone.ok, Icons.check_circle_outline),
      'consented' => ('Consented', Tone.ok, Icons.draw_outlined),
      'enrolled' || 'active' => ('Enrolled', Tone.ok, Icons.how_to_reg_outlined),
      'screen_fail' => ('Screen-fail', Tone.bad, Icons.person_off_outlined),
      _ => (s, Tone.muted, Icons.circle_outlined),
    };

class ScreeningScreen extends StatelessWidget {
  const ScreeningScreen({super.key});
  @override
  Widget build(BuildContext context) => Loader<List>(
        load: (s) => s.run((a) async => await a.get('/screening') as List),
        builder: (c, items, reload) => _Body(items: [for (final x in items) Map<String, dynamic>.from(x as Map)], reload: reload),
      );
}

class _Body extends StatefulWidget {
  final List<Map<String, dynamic>> items;
  final VoidCallback reload;
  const _Body({required this.items, required this.reload});
  @override
  State<_Body> createState() => _BodyState();
}

class _BodyState extends State<_Body> {
  late List<Map<String, dynamic>> items = widget.items;
  String filter = 'screening';
  String? sel;
  String? banner;

  List<Map<String, dynamic>> get shown => [for (final x in items) if (filter == 'all' || x['status'] == filter) x];
  Map<String, dynamic>? get cur => items.where((x) => x['participantId'] == sel).firstOrNull ?? shown.firstOrNull;

  void _replace(Object? r) => setState(() {
        sel ??= cur?['participantId'] as String?; // keep the open candidate after its status leaves the filter
        final n = Map<String, dynamic>.from(r as Map);
        items = [for (final x in items) x['participantId'] == n['participantId'] ? n : x];
      });

  Future<T?> _write<T>(Future<T> Function(Session s) f) async {
    final s = SessionScope.read(context);
    try {
      return await f(s);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      return null;
    }
  }

  Future<void> _confirm(Map<String, dynamic> scr, String cid, String state) async {
    final r = await _write((s) => s.api.post('/participants/${scr['participantId']}/screening/criteria/$cid/confirm', {'status': state}));
    if (r != null) _replace(r);
  }

  Future<void> _signOff(Map<String, dynamic> scr) async {
    final res = await showDialog<Map<String, String>>(context: context, builder: (_) => _SignOffDialog(scr: scr));
    if (res == null) return;
    final r = await _write((s) => s.api.post('/participants/${scr['participantId']}/screening/sign-off', res));
    if (r != null) {
      _replace(r);
      final m = r as Map;
      setState(() => banner = '${statusLook('${m['status']}').$1} · signed off by ${m['coordinatorSignedBy']} at ${fmtTime(m['coordinatorSignedAt'])}');
    }
  }

  Future<void> _step(Map<String, dynamic> scr, String path) async {
    final r = await _write((s) => s.api.post('/participants/${scr['participantId']}/screening/$path'));
    if (r != null) _replace(r);
  }

  Future<void> _rerun(Map<String, dynamic> scr) async {
    final r = await _write((s) => s.api.post('/participants/${scr['participantId']}/screening/check'));
    if (r != null) _replace(r);
  }

  @override
  Widget build(BuildContext context) {
    final s = SessionScope.of(context);
    final toScreen = items.where((x) => x['status'] == 'screening').length;
    final fails = items.where((x) => x['status'] == 'screen_fail').length;
    final scr = cur;
    return Padding(
      padding: const EdgeInsets.all(K.s24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        PageHeader(title: 'Screening', subtitle: '$toScreen to screen · $fails screen-fail · ${items.length} referred. AI proposes, a person decides.'),
        const SizedBox(height: K.s16),
        Expanded(
          child: items.isEmpty
              ? const Panel(child: EmptyState(icon: Icons.fact_check_outlined, title: 'No candidates to screen', hint: 'Sync hospital data to start screening.'))
              : Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  SizedBox(width: 360, child: _Queue(items: shown, all: items, filter: filter, sel: scr?['participantId'], onFilter: (f) => setState(() => filter = f), onSel: (id) => setState(() { sel = id; banner = null; }))),
                  const SizedBox(width: K.s16),
                  Expanded(
                    child: scr == null
                        ? const Panel(child: EmptyState(icon: Icons.rule_outlined, title: 'Nobody in this list', hint: 'Pick another filter.'))
                        : _Checklist(key: ValueKey(scr['participantId']), scr: scr, s: s, banner: banner, onConfirm: (cid, st) => _confirm(scr, cid, st), onSignOff: () => _signOff(scr), onStep: (p) => _step(scr, p), onRerun: () => _rerun(scr)),
                  ),
                ]),
        ),
      ]),
    );
  }
}

class _Queue extends StatelessWidget {
  final List<Map<String, dynamic>> items, all;
  final String filter;
  final String? sel;
  final ValueChanged<String> onFilter, onSel;
  const _Queue({required this.items, required this.all, required this.filter, required this.sel, required this.onFilter, required this.onSel});
  @override
  Widget build(BuildContext context) => Panel(
        padding: EdgeInsets.zero,
        fill: true,
        title: 'Queue',
        trailing: Text('${items.length}', style: K.mono),
        child: Column(children: [
          Padding(
            padding: const EdgeInsets.all(K.s12),
            child: Wrap(spacing: 6, runSpacing: 6, children: [
              for (final f in _filters) ChoiceChip(key: Key('sf-${f.$1}'), label: Text(f.$2), selected: filter == f.$1, onSelected: (_) => onFilter(f.$1)),
            ]),
          ),
          const Divider(),
          Expanded(
            child: items.isEmpty
                ? const EmptyState(icon: Icons.inbox_outlined, title: 'Nothing here', hint: 'Try another filter.')
                : ListView(children: [
                    for (final x in items)
                      DataRow2(
                        key: Key('cand-${x['participantId']}'),
                        height: 64,
                        flex: const [5, 3],
                        selected: x['participantId'] == sel,
                        onTap: () => onSel('${x['participantId']}'),
                        cells: [
                          Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
                            Text('${x['participantId']}', style: numStyle),
                            Text('${x['siteId']} · ${x['metCount']} met · ${x['unknownCount']} unknown', style: K.small),
                          ]),
                          Align(alignment: Alignment.centerRight, child: Builder(builder: (_) {
                            final (l, t, i) = statusLook('${x['status']}');
                            return Pill(l, tone: t, icon: i);
                          })),
                        ],
                      ),
                  ]),
          ),
        ]),
      );
}

class _Checklist extends StatefulWidget {
  final Map<String, dynamic> scr;
  final Session s;
  final String? banner;
  final void Function(String cid, String state) onConfirm;
  final VoidCallback onSignOff, onRerun;
  final void Function(String path) onStep;
  const _Checklist({super.key, required this.scr, required this.s, required this.banner, required this.onConfirm, required this.onSignOff, required this.onStep, required this.onRerun});
  @override
  State<_Checklist> createState() => _ChecklistState();
}

class _ChecklistState extends State<_Checklist> {
  String? open;

  @override
  Widget build(BuildContext context) {
    final scr = widget.scr, s = widget.s;
    final crit = (scr['criteria'] as List).cast<Map>();
    final total = scr['totalCount'] as int, conf = scr['confirmedCount'] as int;
    final status = '${scr['status']}';
    final screening = status == 'screening';
    final canAct = !s.offline && (s.role == 'nurse' || s.role == 'pi');
    final block = s.offline ? 'Reconnect the local backend to write.' : s.isMonitor ? 'Sign-off is a coordinator action.' : null;
    final (sl, st, si) = statusLook(status);
    final canSign = screening && conf == total && total > 0;
    return Panel(
      padding: EdgeInsets.zero,
      fill: true,
      child: ListView(children: [
        Padding(
          padding: const EdgeInsets.all(K.s16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Wrap(spacing: 8, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
              Text('${scr['participantId']}', style: K.title),
              Pill(sl, tone: st, icon: si),
              TextButton(onPressed: () => Navigator.of(context).pushNamed('/participants/${scr['participantId']}'), child: const Text('Open participant')),
              if (screening) ...[
                WriteGate(
                  blockedReason: block ?? (canSign ? null : 'Confirm every criterion first ($conf of $total).'),
                  builder: (en) => FilledButton(key: const Key('signoff'), onPressed: en ? widget.onSignOff : null, child: const Text('Sign off')),
                ),
              ],
              if (status == 'eligible')
                WriteGate(blockedReason: canAct ? null : block, builder: (en) => FilledButton(key: const Key('consent'), onPressed: en ? () => widget.onStep('consent') : null, child: const Text('Record consent'))),
              if (status == 'consented')
                WriteGate(
                  blockedReason: block ?? (s.isPi ? null : 'Only the PI can enrol.'),
                  builder: (en) => FilledButton(key: const Key('enrol'), onPressed: en ? () => widget.onStep('enrol') : null, child: const Text('Enrol')),
                ),
            ]),
            const SizedBox(height: 6),
            Text('${scr['siteId']} · ${scr['metCount']} met · ${scr['notMetCount']} not met · ${scr['unknownCount']} unknown', style: K.small.copyWith(fontSize: 13)),
            const SizedBox(height: 10),
            SizedBox(width: 200, child: Bar(total == 0 ? 0 : conf / total, height: 4)),
            const SizedBox(height: 4),
            Text(conf == 0 ? 'AI proposals only · 0 human-confirmed' : '$conf of $total confirmed by a person', key: const Key('confirmed-count'), style: K.small.copyWith(color: conf == 0 ? K.aiInk : K.ink2)),
            if (scr['screenFailReason'] != null) Padding(padding: const EdgeInsets.only(top: 6), child: Text('Reason: ${scr['screenFailReason']}', style: K.small)),
            if (widget.banner != null)
              Container(
                key: const Key('signed-banner'),
                margin: const EdgeInsets.only(top: K.s12),
                padding: const EdgeInsets.all(K.s12),
                decoration: BoxDecoration(color: K.okBg, border: Border.all(color: K.okLine), borderRadius: BorderRadius.circular(8)),
                child: Text(widget.banner!, style: const TextStyle(color: K.okInk, fontWeight: FontWeight.w500, fontSize: 13)),
              ),
            if (screening && canAct)
              Padding(
                padding: const EdgeInsets.only(top: K.s8),
                child: Wrap(spacing: 8, children: [
                  OutlinedButton(key: const Key('rerun-ai'), onPressed: widget.onRerun, child: const Text('Re-run AI check')),
                  OutlinedButton(
                    key: const Key('confirm-ai-met'),
                    onPressed: () {
                      for (final c in crit) {
                        if (c['coordinatorStatus'] == null && c['aiStatus'] == 'met') widget.onConfirm('${c['criterionId']}', 'met');
                      }
                    },
                    child: const Text('Confirm AI "met" rows'),
                  ),
                ]),
              ),
          ]),
        ),
        for (final t in const ['inclusion', 'exclusion']) ...[
          Container(
            height: 32,
            alignment: Alignment.centerLeft,
            padding: const EdgeInsets.symmetric(horizontal: K.s16),
            color: K.sidebar,
            child: Text('${t.toUpperCase()} (${crit.where((c) => c['type'] == t).length})', style: K.label),
          ),
          for (final c in crit.where((c) => c['type'] == t)) _row(c, canAct && screening),
        ],
      ]),
    );
  }

  Widget _row(Map c, bool canAct) {
    final cid = '${c['criterionId']}';
    final human = c['coordinatorStatus'] != null;
    final ev = (c['evidence'] as List?)?.cast<Map>() ?? const [];
    final isOpen = open == cid;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      DataRow2(
        key: Key('crit-$cid'),
        flex: const [1, 7, 2, 2],
        onTap: () => setState(() => open = isOpen ? null : cid),
        selected: isOpen,
        height: 56,
        cells: [
          Text(cid, style: K.mono),
          Text('${c['text']}', maxLines: 2, overflow: TextOverflow.ellipsis, style: K.body),
          Align(alignment: Alignment.centerLeft, child: StatePill('${c['effectiveStatus']}', human: human)),
          Text(ev.isEmpty ? 'No evidence' : 'Evidence', style: K.small.copyWith(color: ev.isEmpty ? K.ink3 : K.infoInk)),
        ],
      ),
      if (isOpen)
        Container(
          padding: const EdgeInsets.fromLTRB(K.s24, K.s12, K.s16, K.s12),
          color: K.sidebar,
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (ev.isNotEmpty)
              EvidenceBox('${ev.first['text']}', '${c['documentId'] ?? ''} · ${c['provider'] ?? 'rules'} · confidence ${((c['confidence'] as num?) ?? 0).toStringAsFixed(2)}')
            else
              Text('No evidence span. Confirm manually or request the source document.', style: K.small),
            if (c['rationale'] != null) Padding(padding: const EdgeInsets.only(top: 6), child: Text('AI: ${c['rationale']}', style: K.small.copyWith(color: K.aiInk))),
            if (human) Padding(padding: const EdgeInsets.only(top: 6), child: Text('Confirmed by ${c['confirmedBy']} · ${fmtDateTime(c['confirmedAt'])}', style: K.small)),
            const SizedBox(height: K.s8),
            Wrap(spacing: 8, children: [
              if (c['documentId'] != null) TextButton.icon(onPressed: () => showDocument(context, '${c['documentId']}', mark: ev.isEmpty ? null : '${ev.first['text']}'), icon: const Icon(Icons.description_outlined, size: 16), label: const Text('Open source')),
              if (canAct) ...[
                FilledButton(key: Key('met-$cid'), onPressed: () => widget.onConfirm(cid, 'met'), child: const Text('Confirm met')),
                OutlinedButton(key: Key('notmet-$cid'), onPressed: () => widget.onConfirm(cid, 'not_met'), child: const Text('Confirm not met')),
                TextButton(key: Key('unk-$cid'), onPressed: () => widget.onConfirm(cid, 'unknown'), child: const Text('Mark unknown')),
              ],
            ]),
          ]),
        ),
    ]);
  }
}

class _SignOffDialog extends StatefulWidget {
  final Map scr;
  const _SignOffDialog({required this.scr});
  @override
  State<_SignOffDialog> createState() => _SignOffDialogState();
}

class _SignOffDialogState extends State<_SignOffDialog> {
  late String decision = (widget.scr['notMetCount'] as int) > 0 ? 'screen_fail' : 'eligible';
  String reason = 'Did not meet inclusion criteria';
  bool checked = false;
  static const reasons = ['Did not meet inclusion criteria', 'Met an exclusion criterion', 'Withdrew consent', 'Other'];

  @override
  Widget build(BuildContext context) {
    final blocked = decision == 'eligible' && (widget.scr['notMetCount'] as int) > 0;
    return AlertDialog(
      title: const Text('Sign off screening'),
      content: SizedBox(
        width: 440,
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('${widget.scr['metCount']} met · ${widget.scr['notMetCount']} not met · ${widget.scr['unknownCount']} unknown', style: K.body),
          const SizedBox(height: K.s12),
          SegmentedButton<String>(
            segments: const [ButtonSegment(value: 'eligible', label: Text('Eligible'), icon: Icon(Icons.check_circle_outline)), ButtonSegment(value: 'screen_fail', label: Text('Screen-fail'), icon: Icon(Icons.person_off_outlined))],
            selected: {decision},
            onSelectionChanged: (v) => setState(() => decision = v.first),
          ),
          if (decision == 'screen_fail') ...[
            const SizedBox(height: K.s12),
            DropdownButtonFormField<String>(initialValue: reason, decoration: const InputDecoration(labelText: 'Screen-fail reason'), items: [for (final r in reasons) DropdownMenuItem(value: r, child: Text(r))], onChanged: (v) => setState(() => reason = v!)),
          ],
          if (blocked) Padding(padding: const EdgeInsets.only(top: 8), child: Text('A criterion is not met, so this person cannot be eligible.', style: K.small.copyWith(color: K.badInk))),
          CheckboxListTile(key: const Key('checked-all'), contentPadding: EdgeInsets.zero, controlAffinity: ListTileControlAffinity.leading, value: checked, onChanged: (v) => setState(() => checked = v ?? false), title: const Text('I checked every criterion against its source.')),
        ]),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        FilledButton(key: const Key('signoff-submit'), onPressed: checked && !blocked ? () => Navigator.pop(context, {'decision': decision, if (decision == 'screen_fail') 'reason': reason}) : null, child: const Text('Sign off')),
      ],
    );
  }
}
