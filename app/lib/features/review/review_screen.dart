import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../data/app_state.dart';
import 'review_store.dart';

// Spec colours (deliverables/D7_demo_screens.md §1.1, §2.4).
class _Look {
  final Color bg, border, fg;
  final IconData icon;
  final String label;
  final bool dashed;
  const _Look(this.bg, this.border, this.fg, this.icon, this.label, {this.dashed = false});
}

const _ai = _Look(Color(0xFFFFF1CC), Color(0xFF8A5A00), Color(0xFF5A3D00), Icons.auto_awesome, 'AI · Unverified', dashed: true);
const _abst = _Look(Color(0xFFE9EDF3), Color(0xFF5A6B80), Color(0xFF303F52), Icons.help_outline, 'AI abstained', dashed: true);
const _looks = {
  RState.accepted: _Look(Color(0xFFE4F3E9), Color(0xFF1E6B42), Color(0xFF12452A), Icons.check_circle_outline, 'Verified · Accepted'),
  RState.corrected: _Look(Color(0xFFE4F3E9), Color(0xFF1E6B42), Color(0xFF12452A), Icons.edit_note, 'Verified · Corrected'),
  RState.rejected: _Look(Color(0xFFFCE8E6), Color(0xFFA61B1B), Color(0xFF7A1010), Icons.block, 'Rejected'),
  RState.deferred: _Look(Color(0xFFE9EDF3), Color(0xFF5A6B80), Color(0xFF303F52), Icons.schedule, 'Deferred'),
};

_Look _lookOf(ReviewItem i, RState s) =>
    s == RState.unverified ? (i.abstained ? _abst : _ai) : _looks[s]!;

class _Dashed extends CustomPainter {
  final Color c;
  _Dashed(this.c);
  @override
  void paint(Canvas canvas, Size s) {
    final p = Paint()..color = c..style = PaintingStyle.stroke..strokeWidth = 2;
    final path = Path()..addRRect(RRect.fromRectAndRadius(Offset.zero & s, const Radius.circular(8)));
    for (final m in path.computeMetrics()) {
      for (double d = 0; d < m.length; d += 10) {
        canvas.drawPath(m.extractPath(d, d + 5), p);
      }
    }
  }
  @override
  bool shouldRepaint(_Dashed o) => o.c != c;
}

/// Box with the state's colour + (dashed|solid) border; icon+label chip lives inside callers.
class _StateBox extends StatelessWidget {
  final _Look look;
  final Widget child;
  final bool selected;
  const _StateBox._(this.look, this.child, this.selected);
  @override
  Widget build(BuildContext context) => CustomPaint(
        foregroundPainter: look.dashed ? _Dashed(look.border) : null,
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: look.bg,
            borderRadius: BorderRadius.circular(8),
            border: look.dashed ? null : Border.all(color: look.border, width: 2),
            boxShadow: selected ? const [BoxShadow(color: Color(0xFF0B57D0), spreadRadius: 3)] : null,
          ),
          child: child,
        ),
      );
}

Widget _chip(_Look l) => Semantics(
      label: 'Status: ${l.label}',
      excludeSemantics: true,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(color: l.bg, border: Border.all(color: l.border), borderRadius: BorderRadius.circular(4)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(l.icon, size: 16, color: l.fg),
          const SizedBox(width: 4),
          Text(l.label, style: TextStyle(color: l.fg, fontWeight: FontWeight.w600, fontSize: 12)),
        ]),
      ),
    );

class ReviewScreen extends StatefulWidget {
  final String? participantId;
  const ReviewScreen({super.key, this.participantId});
  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  late ReviewStore store;
  String? pid;
  int sel = 0;
  bool correcting = false;
  final edit = TextEditingController();
  String? editError;
  bool _init = false;

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
    store = ReviewStore.of(AppScope.of(context).audit);
    store.load();
  }

  List<ReviewItem> get visible => [for (final i in store.items) if (pid == null || i.participantId == pid) i];
  ReviewItem? get cur => visible.isEmpty ? null : visible[sel.clamp(0, visible.length - 1)];

  bool get _typing => FocusManager.instance.primaryFocus?.context?.widget is EditableText;

  void _move(int d) {
    if (_typing || visible.isEmpty) return;
    setState(() { sel = (sel + d).clamp(0, visible.length - 1); correcting = false; });
  }

  void _next() => _move(1);

  void _accept() {
    final i = cur;
    if (_typing || i == null || !i.canAccept || store.stateOf(i) != RState.unverified) return;
    store.act(i, 'accept');
    _done('${i.label} accepted — verified by $reviewerId');
  }

  void _defer() {
    final i = cur;
    if (_typing || i == null || store.stateOf(i) != RState.unverified) return;
    store.act(i, 'defer');
    _done('${i.label} deferred');
  }

  void _startCorrect() {
    final i = cur;
    if (_typing || i == null || store.stateOf(i) != RState.unverified) return;
    setState(() { correcting = true; editError = null; edit.text = i.abstained ? '' : i.value; });
  }

  void _saveCorrect() {
    final i = cur!;
    final err = store.validate(i, edit.text);
    if (err != null) { setState(() => editError = err); return; }
    store.act(i, 'correct', value: edit.text.trim());
    _done('${i.label} corrected — verified by $reviewerId');
  }

  Future<void> _reject() async {
    final i = cur;
    if (_typing || i == null || store.stateOf(i) != RState.unverified) return;
    final why = await showDialog<String>(context: context, builder: (_) => const _RejectDialog());
    if (why == null || !mounted) return;
    store.act(i, 'reject', why: why);
    _done('${i.label} rejected');
  }

  void _done(String msg) {
    correcting = false;
    // jump to the next pending field
    final v = visible;
    for (var k = 1; k <= v.length; k++) {
      final n = (sel + k) % v.length;
      if (store.stateOf(v[n]) == RState.unverified) { sel = n; break; }
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
            return Center(child: Text('Could not load synthetic data: ${store.error}'));
          }
          if (!store.loaded) return const Center(child: CircularProgressIndicator());
          final i = cur;
          return CallbackShortcuts(
            bindings: {
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
                padding: const EdgeInsets.all(20),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  _toolbar(),
                  const SizedBox(height: 12),
                  Expanded(
                    child: i == null
                        ? const Center(child: Text('No AI extractions in this queue'))
                        : Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                            Expanded(flex: 448, child: _source(i)),
                            const SizedBox(width: 16),
                            Expanded(flex: 320, child: _list()),
                            const SizedBox(width: 16),
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
    final pids = {for (final i in store.items) i.participantId}.toList()..sort();
    return Row(children: [
      Text('AI extraction review', style: Theme.of(context).textTheme.titleLarge),
      const SizedBox(width: 24),
      DropdownButton<String?>(
        value: pid,
        items: [
          const DropdownMenuItem(value: null, child: Text('All participants')),
          for (final p in pids) DropdownMenuItem(value: p, child: Text(p)),
        ],
        onChanged: (v) => setState(() { pid = v; sel = 0; correcting = false; }),
      ),
      const SizedBox(width: 16),
      Text('${store.pending(pid)} pending'),
      const Spacer(),
      const Tooltip(
        message: 'A accept · C correct · X reject · D defer · J/↓ next · K/↑ previous · Esc cancel',
        child: Icon(Icons.keyboard_outlined),
      ),
    ]);
  }

  Widget _pane(String title, Widget body) => Card(
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: Text(title, style: Theme.of(context).textTheme.titleSmall),
          ),
          const Divider(),
          Expanded(child: Scrollbar(child: SingleChildScrollView(padding: const EdgeInsets.all(16), child: body))),
        ]),
      );

  Widget _source(ReviewItem i) {
    final t = i.text;
    final body = i.spanValid
        ? TextSpan(children: [
            TextSpan(text: t.substring(0, i.start)),
            TextSpan(
              text: t.substring(i.start, i.end),
              style: const TextStyle(backgroundColor: Color(0xFFFFC94D), fontWeight: FontWeight.w700, decoration: TextDecoration.underline),
            ),
            TextSpan(text: t.substring(i.end)),
          ])
        : TextSpan(text: t);
    return _pane(
      'SOURCE · ${i.docType} · ${i.docId}',
      Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        if (!i.spanValid)
          Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(8),
            color: const Color(0xFFE9EDF3),
            child: const Text('No evidence span — AI abstained. Accept is disabled.'),
          ),
        SelectableText.rich(TextSpan(style: const TextStyle(fontSize: 15, height: 1.6, color: Color(0xFF1A1C1E)), children: [body])),
      ]),
    );
  }

  Widget _list() {
    final v = visible;
    return _pane(
      'PROPOSED VALUES',
      Column(children: [
        for (var k = 0; k < v.length; k++) ...[
          InkWell(
            key: ValueKey('card-${v[k].id}'),
            onTap: () => setState(() { sel = k; correcting = false; }),
            child: _StateBox._(_lookOf(v[k], store.stateOf(v[k])), _card(v[k]), k == sel),
          ),
          const SizedBox(height: 8),
        ],
      ]),
    );
  }

  Widget _card(ReviewItem i) {
    final s = store.stateOf(i);
    final shown = s == RState.corrected ? store.corrected[i.id]! : i.value;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('${i.participantId} · ${i.label}', style: const TextStyle(fontSize: 12)),
      const SizedBox(height: 4),
      Text('$shown ${i.unit}'.trim(), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
      const SizedBox(height: 8),
      Wrap(spacing: 8, runSpacing: 4, crossAxisAlignment: WrapCrossAlignment.center, children: [
        _chip(_lookOf(i, s)),
        Text('conf ${i.confidence.toStringAsFixed(2)}'),
        if (i.confidence < 0.70 && !i.abstained)
          const Text('Low confidence', style: TextStyle(color: Color(0xFF8A5A00), fontWeight: FontWeight.w700)),
      ]),
    ]);
  }

  Widget _target(ReviewItem i) {
    final s = store.stateOf(i);
    final l = _lookOf(i, s);
    final pending = s == RState.unverified;
    final written = s == RState.accepted ? i.value : s == RState.corrected ? store.corrected[i.id] : null;
    final code = i.code;
    return _pane(
      'TARGET eCRF · ${i.label}',
      Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _StateBox._(
          l,
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            _chip(l),
            const SizedBox(height: 8),
            Text(
              written != null
                  ? '$written ${i.unit}'.trim()
                  : s == RState.rejected
                      ? 'Not entered — rejected: ${store.reason[i.id]}'
                      : pending
                          ? (i.abstained ? 'Not stated in source' : 'Not entered (AI proposes: ${i.value} ${i.unit})'.replaceAll(' )', ')'))
                          : 'Pending review',
              style: TextStyle(fontSize: 16, color: l.fg, fontWeight: FontWeight.w600),
            ),
            if (written != null) Text('Verified by $reviewerId', style: TextStyle(color: l.fg)),
          ]),
          false,
        ),
        const SizedBox(height: 12),
        Text('Confidence ${i.confidence.toStringAsFixed(2)}${i.confidence < 0.70 && !i.abstained ? ' · Low confidence' : ''}'),
        if (code != null)
          Text('Code ${code['system']} ${code['code']} — ${code['display']}'
              '${code['codeVerified'] == true ? '' : ' (placeholder, unverified)'}'),
        Text('Model ${i.model} · prompt ${i.prompt}'),
        const SizedBox(height: 16),
        if (correcting)
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            TextField(
              controller: edit,
              autofocus: true,
              decoration: InputDecoration(labelText: 'Corrected value', suffixText: i.unit, errorText: editError, border: const OutlineInputBorder()),
              onSubmitted: (_) => _saveCorrect(),
            ),
            const SizedBox(height: 8),
            Row(children: [
              FilledButton(onPressed: _saveCorrect, child: const Text('Save correction')),
              const SizedBox(width: 8),
              TextButton(onPressed: () => setState(() => correcting = false), child: const Text('Cancel')),
            ]),
          ])
        else
          Wrap(spacing: 8, runSpacing: 8, children: [
            FilledButton(onPressed: pending && i.canAccept ? _accept : null, child: const Text('Accept')),
            FilledButton.tonal(onPressed: pending ? _startCorrect : null, child: const Text('Correct')),
            TextButton(onPressed: pending ? _reject : null, child: const Text('Reject')),
            OutlinedButton(onPressed: pending ? _defer : null, child: const Text('Defer')),
          ]),
        if (pending && !i.canAccept)
          const Padding(padding: EdgeInsets.only(top: 8), child: Text('Accept disabled: no evidence in source. Correct, reject or defer.')),
        const SizedBox(height: 12),
        TextButton(onPressed: () => Navigator.of(context).pushReplacementNamed('/audit'), child: const Text('View audit trail')),
      ]),
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
