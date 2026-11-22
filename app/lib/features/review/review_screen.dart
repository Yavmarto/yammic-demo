import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../data/session.dart';
import '../../theme/tokens.dart';
import '../../ui/widgets.dart';
import 'review_store.dart';

// Provenance semantics (deliverables/D7_demo_screens.md §1.1, §2.4):
// amber dashed = AI proposal, green solid = human verified, red = rejected, grey = neutral.
class _Look {
  final Tone tone;
  final IconData icon;
  final String label;
  final bool dashed;
  const _Look(this.tone, this.icon, this.label, {this.dashed = false});
  Color get bg => toneColors(tone).$1;
  Color get border => toneColors(tone).$2;
  Color get fg => toneColors(tone).$3;
}

_Look _lookOf(ReviewItem i, RState s) => switch (s) {
      RState.unverified => i.abstained
          ? const _Look(Tone.muted, Icons.help_outline, 'AI abstained', dashed: true)
          : const _Look(Tone.ai, Icons.auto_awesome, 'AI · Unverified', dashed: true),
      RState.accepted => const _Look(Tone.ok, Icons.check_circle_outline, 'Verified · Accepted'),
      RState.corrected => i.provider == 'human' ? const _Look(Tone.ok, Icons.person, 'Entered by a person') : const _Look(Tone.ok, Icons.edit_note, 'Verified · Corrected'),
      RState.rejected => const _Look(Tone.bad, Icons.block, 'Rejected'),
      RState.deferred => const _Look(Tone.muted, Icons.schedule, 'Deferred'),
    };

class _Dashed extends CustomPainter {
  final Color c;
  _Dashed(this.c);
  @override
  void paint(Canvas canvas, Size s) {
    final p = Paint()..color = c..style = PaintingStyle.stroke..strokeWidth = 1.5;
    final path = Path()..addRRect(RRect.fromRectAndRadius(Offset.zero & s, const Radius.circular(10)));
    for (final m in path.computeMetrics()) {
      for (double d = 0; d < m.length; d += 9) {
        canvas.drawPath(m.extractPath(d, d + 5), p);
      }
    }
  }
  @override
  bool shouldRepaint(_Dashed o) => o.c != c;
}

/// Box with the state's colour + (dashed|solid) border.
class _StateBox extends StatelessWidget {
  final _Look look;
  final Widget child;
  final bool selected;
  const _StateBox._(this.look, this.child, this.selected);
  @override
  Widget build(BuildContext context) => CustomPaint(
        foregroundPainter: look.dashed ? _Dashed(look.border) : null,
        child: AnimatedContainer(
          duration: K.fast,
          curve: K.ease,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: look.bg,
            borderRadius: BorderRadius.circular(10),
            border: look.dashed ? null : Border.all(color: look.border, width: 1.5),
            boxShadow: selected ? const [BoxShadow(color: K.accent, spreadRadius: 2)] : null,
          ),
          child: child,
        ),
      );
}

Widget _chip(_Look l) => Pill(l.label, tone: l.tone, icon: l.icon);

class ReviewScreen extends StatefulWidget {
  final String? participantId;
  const ReviewScreen({super.key, this.participantId});
  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  late ReviewStore store;
  late Session session;
  Map? run; // live extraction run being polled
  bool _polling = false;
  String? pid;
  int sel = 0;
  bool correcting = false;
  bool manual = false, savingManual = false;
  List<dynamic> manualFields = [], manualDocs = [];
  String? manualField, manualDoc, manualText, manualError;
  final manualValue = TextEditingController(), manualEvidence = TextEditingController();
  final edit = TextEditingController();
  String? editError;
  bool _init = false;
  bool mineOnly = false;

  @override
  void initState() {
    super.initState();
    pid = widget.participantId;
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_init) return;
    _init = true;
    session = SessionScope.read(context);
    store = ReviewStore(session)..load();
  }

  List<ReviewItem> get visible => [for (final i in store.items) if ((pid == null || i.participantId == pid) && (!mineOnly || i.assignedTo == session.username)) i];
  ReviewItem? get cur => visible.isEmpty ? null : visible[sel.clamp(0, visible.length - 1)];

  Future<void> _openManual() async {
    if (pid == null) return;
    try {
      final form = await session.api.get('/participants/$pid/ecrf') as Map;
      final docs = await session.api.get('/participants/$pid/documents') as List;
      if (!mounted) return;
      setState(() {
        manualFields = (form['fields'] as List).where((f) => f['value'] == null && !store.items.any((i) => i.participantId == pid && i.field == f['id'] && i.state == RState.unverified && !i.abstained)).toList();
        manualDocs = docs; manualField = null; manualDoc = null; manualText = null; manualError = null;
        manualValue.clear(); manualEvidence.clear(); manual = true;
      });
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not load entry form: $e')));
    }
  }

  Future<void> _selectManualDoc(String? id) async {
    setState(() { manualDoc = id; manualText = null; });
    if (id == null) return;
    try {
      final doc = await session.api.get('/documents/$id') as Map;
      if (mounted && manualDoc == id) setState(() => manualText = doc['text'] as String);
    } catch (e) {
      if (mounted) setState(() => manualError = 'Could not load document: $e');
    }
  }

  Future<void> _saveManual() async {
    if (savingManual) return;
    if (manualField == null || manualDoc == null || manualValue.text.trim().isEmpty || manualEvidence.text.trim().isEmpty) {
      setState(() => manualError = 'Choose a field and document, and enter a value and source quote.'); return;
    }
    if (manualText == null || !manualText!.contains(manualEvidence.text.trim())) {
      setState(() => manualError = 'The quote must match the selected document exactly.'); return;
    }
    setState(() { savingManual = true; manualError = null; });
    try {
      final result = await session.api.post('/participants/$pid/ecrf/$manualField/manual', {
        'value': manualValue.text.trim(), 'documentId': manualDoc, 'evidence': manualEvidence.text.trim(),
      }) as Map;
      await store.load();
      if (!mounted) return;
      final selected = visible.indexWhere((i) => i.id == result['extraction']['id']);
      setState(() { manual = false; sel = selected < 0 ? 0 : selected; });
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Value saved as entered by a person.')));
    } catch (e) {
      if (mounted) setState(() => manualError = 'Could not save: $e');
    } finally {
      if (mounted) setState(() => savingManual = false);
    }
  }

  Widget _manualPanel() => Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
    Expanded(child: _pane('Source document', Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      DropdownButtonFormField<String>(initialValue: manualDoc, decoration: const InputDecoration(labelText: 'Document'),
        items: [for (final d in manualDocs) DropdownMenuItem(value: d['id'] as String, child: Text('${d['title']} (${d['id']})', overflow: TextOverflow.ellipsis))], onChanged: _selectManualDoc),
      const SizedBox(height: 16), SelectableText(manualText ?? 'Choose a document to see its text.'),
    ]))),
    const SizedBox(width: K.s16),
    Expanded(child: _pane('Enter from source', Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      const Text('Enter an empty field from the document. Copy the exact source quote as evidence.'),
      const SizedBox(height: 16),
      DropdownButtonFormField<String>(initialValue: manualField, decoration: const InputDecoration(labelText: 'Empty field'),
        items: [for (final f in manualFields) DropdownMenuItem(value: f['id'] as String, child: Text('${f['label']} (${f['id']})'))], onChanged: (v) => setState(() => manualField = v)),
      const SizedBox(height: 16), TextField(controller: manualValue, decoration: const InputDecoration(labelText: 'Value')),
      const SizedBox(height: 16), TextField(controller: manualEvidence, maxLines: 3, decoration: const InputDecoration(labelText: 'Exact source quote')),
      if (manualError != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(manualError!, style: const TextStyle(color: K.badInk))),
      const SizedBox(height: 16), FilledButton(onPressed: savingManual ? null : _saveManual, child: Text(savingManual ? 'Saving…' : 'Save as person-entered')),
      TextButton(onPressed: savingManual ? null : () => setState(() => manual = false), child: const Text('Cancel')),
    ]))),
  ]);

  bool get _typing => FocusManager.instance.primaryFocus?.context?.widget is EditableText;

  void _move(int d) {
    if (_typing || visible.isEmpty) return;
    setState(() { sel = (sel + d).clamp(0, visible.length - 1); correcting = false; });
  }

  void _next() => _move(1);

  bool get _canAct => session.canWrite && (session.isPi || cur?.assignedTo == null || cur?.assignedTo == session.username);

  Future<bool> _write(ReviewItem i, String action, {String? value, String? why}) async {
    final err = await store.act(i, action, value: value, why: why);
    if (err != null && mounted) {
      ScaffoldMessenger.of(context)
        ..clearSnackBars()
        ..showSnackBar(SnackBar(content: Text('Could not save: $err')));
    }
    return err == null;
  }

  Future<void> _accept() async {
    final i = cur;
    if (_typing || !_canAct || i == null || !i.canAccept || (i.state != RState.unverified && i.state != RState.deferred)) return;
    if (await _write(i, 'accept') && mounted) _done('${i.label} accepted — verified by ${session.username}');
  }

  Future<void> _defer() async {
    final i = cur;
    if (_typing || !_canAct || i == null || (i.state != RState.unverified && i.state != RState.deferred)) return;
    if (await _write(i, 'defer') && mounted) _done('${i.label} deferred');
  }

  void _startCorrect() {
    final i = cur;
    if (_typing || !_canAct || i == null || (i.state != RState.unverified && i.state != RState.deferred)) return;
    setState(() { correcting = true; editError = null; edit.text = i.abstained ? '' : i.value; });
  }

  Future<void> _saveCorrect() async {
    final i = cur!;
    final err = store.validate(i, edit.text);
    if (err != null) { setState(() => editError = err); return; }
    if (await _write(i, 'correct', value: edit.text.trim()) && mounted) _done('${i.label} corrected — verified by ${session.username}');
  }

  Future<void> _reject() async {
    final i = cur;
    if (_typing || !_canAct || i == null || (i.state != RState.unverified && i.state != RState.deferred)) return;
    final why = await showDialog<String>(context: context, builder: (_) => const _RejectDialog());
    if (why == null || !mounted) return;
    if (await _write(i, 'reject', why: why) && mounted) _done('${i.label} rejected');
  }

  void _done(String msg) {
    correcting = false;
    // jump to the next pending field
    final v = visible;
    for (var k = 1; k <= v.length; k++) {
      final n = (sel + k) % v.length;
      if (v[n].state == RState.unverified) { sel = n; break; }
    }
    setState(() {});
    ScaffoldMessenger.of(context)
      ..clearSnackBars()
      ..showSnackBar(SnackBar(content: Text(msg), duration: const Duration(seconds: 3)));
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
        listenable: store,
        builder: (context, _) {
          if (store.error != null) {
            return ErrorState(
              message: '${store.error}',
              onRetry: () { store.load(); setState(() {}); },
            );
          }
          if (!store.loaded) return const PageSkeleton();
          final i = cur;
          return CallbackShortcuts(
            bindings: manual ? {} : {
              const SingleActivator(LogicalKeyboardKey.keyA): _accept,
              const SingleActivator(LogicalKeyboardKey.keyX): _reject,
              const SingleActivator(LogicalKeyboardKey.keyD): _defer,
              const SingleActivator(LogicalKeyboardKey.keyC): _startCorrect,
              const SingleActivator(LogicalKeyboardKey.keyJ): _next,
              const SingleActivator(LogicalKeyboardKey.arrowDown): _next,
              const SingleActivator(LogicalKeyboardKey.keyK): () => _move(-1),
              const SingleActivator(LogicalKeyboardKey.arrowUp): () => _move(-1),
              const SingleActivator(LogicalKeyboardKey.escape): () { if (correcting) setState(() => correcting = false); },
            },
            child: Focus(
              autofocus: true,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(K.s32, 28, K.s32, K.s24),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  _toolbar(),
                  const SizedBox(height: K.s16),
                  Expanded(
                    child: manual ? _manualPanel() : i == null
                        ? const Panel(child: SizedBox(height: 240, child: EmptyState(icon: Icons.fact_check_outlined, title: 'Queue is empty', hint: 'No AI extractions for this selection. Pick another participant.')))
                        : Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                            Expanded(flex: 448, child: _source(i)),
                            const SizedBox(width: K.s16),
                            Expanded(flex: 320, child: _list()),
                            const SizedBox(width: K.s16),
                            Expanded(flex: 360, child: _target(i)),
                          ]),
                  ),
                ]),
              ),
            ),
          );
        },
      );

  Widget _toolbar() {
    final pids = store.participantIds;
    final total = visible.length, left = visible.where((i) => i.state == RState.unverified || i.state == RState.deferred).length;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      PageHeader(
        title: 'AI extraction review',
        subtitle: 'Check each proposed value against its source before it enters the eCRF.',
        trailing: Row(mainAxisSize: MainAxisSize.min, children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(color: K.surface, border: Border.all(color: K.lineStrong), borderRadius: BorderRadius.circular(8)),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String?>(
                value: pid,
                isDense: false,
                borderRadius: BorderRadius.circular(10),
                style: K.body.copyWith(fontWeight: FontWeight.w500),
                items: [
                  const DropdownMenuItem(value: null, child: Text('All participants')),
                  for (final p in pids) DropdownMenuItem(value: p, child: Text(p)),
                ],
                onChanged: (v) => setState(() { pid = v; sel = 0; correcting = false; manual = false; }),
              ),
            ),
          ),
          const SizedBox(width: K.s12),
          WriteGate(
            blockedReason: session.writeBlockedReason ?? (pid == null ? 'Pick a participant first.' : null),
            builder: (en) => OutlinedButton.icon(
              onPressed: en && run == null ? _startRun : null,
              icon: const Icon(Icons.play_arrow_rounded, size: 18),
              label: const Text('Run extraction'),
            ),
          ),
          const SizedBox(width: K.s12),
          OutlinedButton.icon(onPressed: _canAct && pid != null ? _openManual : null, icon: const Icon(Icons.edit_note), label: const Text('Enter from source')),
          const SizedBox(width: K.s12),
          const Tooltip(
            message: 'A accept · C correct · X reject · D defer · J/↓ next · K/↑ previous · Esc cancel',
            child: Padding(padding: EdgeInsets.all(8), child: Icon(Icons.keyboard_outlined, color: K.ink2)),
          ),
        ]),
      ),
      Row(children: [
        Checkbox(value: mineOnly, onChanged: (v) => setState(() { mineOnly = v ?? false; sel = 0; })),
        const Text("My assigned work"),
      ]),
      if (run != null) _runBar(),
      const SizedBox(height: K.s16),
      Row(children: [
        SizedBox(width: 260, child: Bar(total == 0 ? 0 : (total - left) / total, color: K.okLine)),
        const SizedBox(width: 12),
        Text('${total - left} of $total reviewed', style: K.small),
        const SizedBox(width: 8),
        Text('·', style: K.small),
        const SizedBox(width: 8),
        Text('$left pending', style: K.small.copyWith(fontWeight: FontWeight.w500, color: left > 0 ? K.aiInk : K.okInk)),
      ]),
    ]);
  }

  Future<void> _startRun() async {
    setState(() => run = {'status': 'queued', 'done': 0, 'total': 0});
    try {
      run = await session.api.post('/participants/$pid/extract?provider=auto') as Map;
    } catch (e) {
      setState(() => run = {'status': 'failed', 'error': '$e', 'done': 0, 'total': 0});
      return;
    }
    setState(() {});
    _poll();
  }

  Future<void> _poll() async {
    if (_polling) return;
    _polling = true;
    final started = DateTime.now();
    while (mounted && run != null && run!['status'] != 'completed' && run!['status'] != 'failed') {
      await Future.delayed(const Duration(milliseconds: 700));
      try {
        final r = await session.api.get('/runs/${run!['id']}') as Map;
        if (mounted) setState(() => run = r);
      } catch (_) {}
      if (DateTime.now().difference(started).inSeconds > 90 && mounted) {
        setState(() => run = {...?run, 'status': 'failed', 'error': 'Timed out. Is the AI service running?'});
      }
    }
    _polling = false;
    if (mounted && run?['status'] == 'completed') {
      await store.load();
      if (mounted) setState(() {});
    }
  }

  /// Live extraction run: provider/model, progress, and the outcome.
  Widget _runBar() {
    final st = '${run!['status']}', done = (run!['done'] as num?)?.toInt() ?? 0, total = (run!['total'] as num?)?.toInt() ?? 0;
    final fin = st == 'completed' || st == 'failed';
    return Container(
      margin: const EdgeInsets.only(top: K.s12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: st == 'failed' ? K.badBg : K.aiBg, borderRadius: BorderRadius.circular(10), border: Border.all(color: st == 'failed' ? K.badLine : K.aiLine.withValues(alpha: .5))),
      child: Row(children: [
        Icon(st == 'failed' ? Icons.error_outline : st == 'completed' ? Icons.check_circle_outline : Icons.auto_awesome, size: 18, color: st == 'failed' ? K.badInk : K.aiInk),
        const SizedBox(width: 10),
        Text(
          st == 'failed' ? 'Extraction failed: ${run!['error']}' : st == 'completed' ? 'Extraction complete · $done proposals added for review' : 'Extraction ${st == 'queued' ? 'queued' : 'running'}${run!['provider'] != null ? ' · ${run!['provider']}' : ''}…',
          style: K.small.copyWith(color: st == 'failed' ? K.badInk : K.aiInk, fontWeight: FontWeight.w500),
        ),
        const SizedBox(width: 16),
        if (!fin) Expanded(child: Bar(total == 0 ? 0 : done / total, color: K.aiLine, height: 4)) else const Spacer(),
        if (fin) TextButton(onPressed: () => setState(() => run = null), child: const Text('Dismiss')),
      ]),
    );
  }

  Widget _pane(String title, Widget body) => DecoratedBox(
        decoration: BoxDecoration(color: K.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: K.line)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(K.s16, 14, K.s16, 12),
            child: Text(title.toUpperCase(), style: K.label, overflow: TextOverflow.ellipsis),
          ),
          const Divider(),
          Expanded(child: Scrollbar(child: SingleChildScrollView(padding: const EdgeInsets.all(K.s16), child: body))),
        ]),
      );

  Widget _source(ReviewItem i) {
    final t = i.text;
    final body = i.spanValid
        ? TextSpan(children: [
            TextSpan(text: t.substring(0, i.start)),
            TextSpan(
              text: t.substring(i.start, i.end),
              style: const TextStyle(backgroundColor: Color(0xFFFFE3A1), fontWeight: FontWeight.w500, decoration: TextDecoration.underline, decorationColor: K.aiLine),
            ),
            TextSpan(text: t.substring(i.end)),
          ])
        : TextSpan(text: t);
    return _pane(
      'Source · ${i.docType} · ${i.docId}',
      Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        if (!i.spanValid)
          Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: K.mutedBg, borderRadius: BorderRadius.circular(8)),
            child: const Row(children: [
              Icon(Icons.help_outline, size: 18, color: K.mutedInk),
              SizedBox(width: 8),
              Expanded(child: Text('No evidence span: the AI abstained. Accept is disabled.', style: K.small)),
            ]),
          ),
        SelectableText.rich(TextSpan(style: const TextStyle(fontSize: 14.5, height: 1.7, color: K.ink), children: [body])),
      ]),
    );
  }

  Widget _list() {
    final v = visible;
    return _pane(
      'Proposed values · ${v.length}',
      Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        for (var k = 0; k < v.length; k++) ...[
          InkWell(
            key: ValueKey('card-${v[k].id}'),
            borderRadius: BorderRadius.circular(10),
            onTap: () => setState(() { sel = k; correcting = false; }),
            child: _StateBox._(_lookOf(v[k], v[k].state), _card(v[k]), k == sel),
          ),
          const SizedBox(height: 10),
        ],
      ]),
    );
  }

  Widget _card(ReviewItem i) {
    final s = i.state;
    final shown = s == RState.corrected ? (i.correctedValue ?? '') : i.value;
    final low = i.confidence < 0.70 && !i.abstained;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('${i.participantId} · ${i.label}', style: K.small),
      Text(i.assignedTo == null ? 'Unassigned' : 'Assigned to ${i.assignedTo} · Due ${i.dueDate}', style: K.small),
      const SizedBox(height: 4),
      Text('$shown ${i.unit}'.trim(), style: K.heading.copyWith(fontSize: 16)),
      const SizedBox(height: 10),
      Wrap(spacing: 8, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center, children: [
        _chip(_lookOf(i, s)),
        Text('conf ${i.confidence.toStringAsFixed(2)}', style: K.small),
        if (low) const Pill('Low confidence', tone: Tone.bad, icon: Icons.warning_amber_rounded),
      ]),
    ]);
  }

  Widget _kv(String k, String v) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 5),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SizedBox(width: 92, child: Text(k, style: K.small)),
          Expanded(child: Text(v, style: K.body.copyWith(fontSize: 13))),
        ]),
      );

  Widget _act(String label, String key, VoidCallback? onTap, {bool primary = false, bool danger = false}) {
    final kb = Kbd(key, color: primary ? Colors.white70 : null);
    final row = Row(children: [Text(label), const Spacer(), kb]);
    return SizedBox(
      width: double.infinity,
      child: primary
          ? FilledButton(onPressed: onTap, child: row)
          : danger
              ? TextButton(style: TextButton.styleFrom(foregroundColor: K.badInk), onPressed: onTap, child: row)
              : OutlinedButton(onPressed: onTap, child: row),
    );
  }

  Future<void> _assign(ReviewItem item) async {
    try {
      final reviewers = await session.api.get('/reviewers') as List;
      if (!mounted) return;
      String? reviewer = item.assignedTo ?? (reviewers.isEmpty ? null : reviewers.first['username'] as String);
      DateTime? due = DateTime.tryParse(item.dueDate ?? '');
      final choice = await showDialog<bool>(context: context, builder: (context) => StatefulBuilder(builder: (context, update) => AlertDialog(
        title: const Text('Assign review'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          DropdownButton<String>(value: reviewer, hint: const Text('Select reviewer'), isExpanded: true,
            items: [for (final r in reviewers) DropdownMenuItem<String>(value: r['username'] as String, child: Text(r['name'] as String))],
            onChanged: (v) => update(() => reviewer = v)),
          TextButton(onPressed: () async {
            final selected = await showDatePicker(context: context, initialDate: due ?? Session.demoToday,
              firstDate: DateTime(2020), lastDate: DateTime(2100));
            if (selected != null) update(() => due = selected);
          }, child: Text(due == null ? 'Select due date' : 'Due ${due!.toIso8601String().substring(0, 10)}')),
        ]),
        actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(onPressed: reviewer == null || due == null ? null : () => Navigator.pop(context, true), child: const Text('Save'))],
      )));
      if (choice != true) return;
      final result = await session.api.post('/extractions/${item.id}/assignment', {'assignedTo': reviewer, 'dueDate': due!.toIso8601String().substring(0, 10)}) as Map;
      setState(() => item.j = Map<String, dynamic>.from(result));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Assignment failed: $e')));
    }
  }

  Widget _target(ReviewItem i) {
    final s = i.state;
    final l = _lookOf(i, s);
    final pending = s == RState.unverified || s == RState.deferred;
    final written = s == RState.accepted ? i.value : s == RState.corrected ? i.correctedValue : null;
    final code = i.code;
    final low = i.confidence < 0.70 && !i.abstained;
    return _pane(
      'Target eCRF · ${i.label}',
      AnimatedSwitcher(
        duration: const Duration(milliseconds: 180),
        child: Column(
          key: ValueKey('${i.id}-$s-$correcting'),
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _StateBox._(
              l,
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                _chip(l),
                const SizedBox(height: 10),
                Text(
                  written != null
                      ? '$written ${i.unit}'.trim()
                      : s == RState.rejected
                          ? 'Not entered. Rejected: ${i.reason}'
                          : pending
                              ? (i.abstained ? 'Not stated in source' : 'Not entered (AI proposes: ${i.value} ${i.unit})'.replaceAll(' )', ')'))
                              : 'Pending review',
                  style: K.heading.copyWith(fontSize: 16, color: l.fg),
                ),
                if (written != null) Padding(padding: const EdgeInsets.only(top: 4), child: Text('Verified by ${i.last?['username'] ?? session.username}', style: K.small.copyWith(color: l.fg))),
              ]),
              false,
            ),
            if (i.assignedTo != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text('Assigned to ${i.assignedTo} · Due ${i.dueDate}', style: K.small)),
            if (session.isPi && !session.offline && pending) TextButton.icon(onPressed: () => _assign(i), icon: const Icon(Icons.person_add_alt), label: const Text('Assign or change due date')),
            const SizedBox(height: K.s16),
            Row(children: [
              const SizedBox(width: 92, child: Text('Confidence', style: K.small)),
              Expanded(child: Bar(i.confidence, color: low ? K.badLine : K.accent, height: 5)),
              const SizedBox(width: 10),
              Text(i.confidence.toStringAsFixed(2), style: K.mono),
            ]),
            if (low) Padding(padding: const EdgeInsets.only(top: 6, left: 92), child: Text('Low confidence: check the source closely.', style: K.small.copyWith(color: K.badInk))),
            const SizedBox(height: 6),
            if (code != null)
              _kv('Code', '${code['system']} ${code['code']} (${code['display']})'
                  '${code['codeVerified'] == true ? '' : ' · placeholder, unverified'}'),
            _kv('Model', i.model),
            _kv('Prompt', i.prompt),
            _kv('Provider', i.provider),
            const SizedBox(height: K.s16),
            if (correcting)
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                TextField(
                  controller: edit,
                  autofocus: true,
                  decoration: InputDecoration(labelText: 'Corrected value', suffixText: i.unit, errorText: editError),
                  onSubmitted: (_) => _saveCorrect(),
                ),
                const SizedBox(height: 12),
                Wrap(spacing: 8, runSpacing: 8, children: [
                  FilledButton(onPressed: _saveCorrect, child: const Text('Save correction')),
                  TextButton(onPressed: () => setState(() => correcting = false), child: const Text('Cancel')),
                ]),
              ])
            else
              Column(children: [
                _act('Accept', 'A', pending && i.canAccept && _canAct ? _accept : null, primary: true),
                const SizedBox(height: 8),
                _act('Correct', 'C', pending && _canAct ? _startCorrect : null),
                const SizedBox(height: 8),
                Row(children: [
                  Expanded(child: _act('Defer', 'D', pending && _canAct ? _defer : null)),
                  const SizedBox(width: 8),
                  Expanded(child: _act('Reject', 'X', pending && _canAct ? _reject : null, danger: true)),
                ]),
              ]),
            if (pending && !_canAct)
              Padding(padding: const EdgeInsets.only(top: 10), child: Text(session.writeBlockedReason ?? 'Assigned to another reviewer.', style: K.small)),
            if (pending && _canAct && !i.canAccept)
              const Padding(padding: EdgeInsets.only(top: 10), child: Text('Accept is disabled: no evidence in source. Correct, reject or defer.', style: K.small)),
            const SizedBox(height: K.s16),
            const Divider(),
            const SizedBox(height: 4),
            TextButton.icon(
              onPressed: () => Navigator.of(context).pushReplacementNamed('/audit', arguments: i.participantId),
              icon: const Icon(Icons.history, size: 18),
              label: const Text('View audit trail'),
            ),
          ],
        ),
      ),
    );
  }
}

class _RejectDialog extends StatefulWidget {
  const _RejectDialog();
  @override
  State<_RejectDialog> createState() => _RejectDialogState();
}

class _RejectDialogState extends State<_RejectDialog> {
  static const reasons = ['Wrong patient', 'Not in source', 'Wrong field', 'Duplicate'];
  String? r;
  @override
  Widget build(BuildContext context) => AlertDialog(
        title: const Text('Reject AI value — reason required'),
        content: RadioGroup<String>(
          groupValue: r,
          onChanged: (v) => setState(() => r = v),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            for (final x in reasons) RadioListTile<String>(value: x, title: Text(x)),
          ]),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(onPressed: r == null ? null : () => Navigator.pop(context, r), child: const Text('Reject')),
        ],
      );
}
