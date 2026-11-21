import 'package:flutter/material.dart';
import '../data/session.dart';
import '../theme/tokens.dart';
import 'format.dart';
import 'widgets.dart';

/// Finding + verification in one pill (D7c 1.3): AI proposals are amber with a sparkle, human-confirmed are solid.
class StatePill extends StatelessWidget {
  final String finding; // met | not_met | unknown
  final bool human;
  const StatePill(this.finding, {super.key, required this.human});
  @override
  Widget build(BuildContext context) {
    final (label, icon, humanTone) = switch (finding) {
      'met' => ('Met', Icons.check_circle_outline, Tone.ok),
      'not_met' => ('Not met', Icons.block, Tone.bad),
      _ => ('Unknown', Icons.help_outline, Tone.muted),
    };
    if (human || finding == 'unknown') return Pill(human ? label : '$label · AI', tone: humanTone, icon: icon);
    return Pill('$label · AI', tone: Tone.ai, icon: Icons.auto_awesome);
  }
}

/// Quote with the v3 evidence highlight and a meta line.
class EvidenceBox extends StatelessWidget {
  final String quote, meta;
  const EvidenceBox(this.quote, this.meta, {super.key});
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(K.s12),
        decoration: BoxDecoration(color: K.surface, border: Border.all(color: K.line), borderRadius: BorderRadius.circular(8)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            decoration: const BoxDecoration(color: Color(0xFFFFE1A8), border: Border(bottom: BorderSide(color: K.aiLine, width: 2))),
            child: Text(quote, style: K.body),
          ),
          const SizedBox(height: 6),
          Text(meta, style: K.small),
        ]),
      );
}

/// Opens a source document in a dialog, never navigates away. `mark` highlights an excerpt.
Future<void> showDocument(BuildContext context, String id, {String? mark}) async {
  final s = SessionScope.read(context);
  final d = await s.run((a) async => await a.get('/documents/$id') as Map);
  if (!context.mounted) return;
  final text = '${d['text']}';
  final i = mark == null || mark.isEmpty ? -1 : text.indexOf(mark);
  showDialog(
    context: context,
    builder: (c) => Dialog(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 760, maxHeight: 640),
        child: Padding(
          padding: const EdgeInsets.all(K.s24),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(child: Text('${d['title']}', style: K.title)),
              IconButton(tooltip: 'Close', onPressed: () => Navigator.pop(c), icon: const Icon(Icons.close)),
            ]),
            Text('${d['id']} · ${fmtDate(d['documentDate'])}', style: K.mono),
            const Divider(height: 24),
            Expanded(
              child: SingleChildScrollView(
                child: SelectableText.rich(TextSpan(style: const TextStyle(fontSize: 14.5, height: 1.65, color: K.ink), children: [
                  if (i < 0) TextSpan(text: text) else ...[
                    TextSpan(text: text.substring(0, i)),
                    TextSpan(text: mark, style: const TextStyle(backgroundColor: Color(0xFFFFE1A8))),
                    TextSpan(text: text.substring(i + mark!.length)),
                  ],
                ])),
              ),
            ),
          ]),
        ),
      ),
    ),
  );
}
