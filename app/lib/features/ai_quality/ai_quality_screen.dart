import 'package:flutter/material.dart';
import '../../api/api.dart';
import '../../data/session.dart';
import '../../theme/tokens.dart';
import '../../ui/async.dart';
import '../../ui/format.dart';
import '../../ui/widgets.dart';

class _Q {
  final Map evals; // provider name -> eval result
  final List providers, prompts;
  _Q(this.evals, this.providers, this.prompts);
}

Future<_Q> _load(Session s) => s.run((a) async {
      final evals = <String, Map>{};
      try {
        final r = await a.get('/ai/eval') as Map;
        final all = r['providers'] as Map?;
        if (all != null && all.isNotEmpty) {
          for (final e in all.entries) {
            evals['${e.key}'] = e.value as Map;
          }
        } else {
          final res = r['results'] as Map;
          evals['${res['provider']['name']}'] = res;
        }
      } on ApiException catch (e) {
        if (e.status != 404) rethrow;
      }
      final pr = (await a.get('/ai/providers') as Map)['providers'] as List;
      final pm = (await a.get('/ai/prompts') as Map)['prompts'] as List;
      return _Q(evals, pr, pm);
    });

class AiQualityScreen extends StatefulWidget {
  const AiQualityScreen({super.key});
  @override
  State<AiQualityScreen> createState() => _AiQualityState();
}

class _AiQualityState extends State<AiQualityScreen> {
  String? sel;
  @override
  Widget build(BuildContext context) => Loader<_Q>(
        load: _load,
        builder: (c, q, reload) {
          final names = q.evals.keys.cast<String>().toList();
          final cur = q.evals[sel ?? (names.isEmpty ? null : names.first)] as Map?;
          return SingleChildScrollView(
            padding: const EdgeInsets.all(K.s24),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              PageHeader(
                title: 'AI quality',
                subtitle: 'Precision and recall against the gold set, per field and provider. Quality is measured before it is trusted.',
                trailing: names.length > 1
                    ? SegmentedButton<String>(
                        showSelectedIcon: false,
                        segments: [for (final n in names) ButtonSegment(value: n, label: Text(n))],
                        selected: {sel ?? names.first},
                        onSelectionChanged: (v) => setState(() => sel = v.first),
                      )
                    : null,
              ),
              const SizedBox(height: K.s16),
              if (cur == null)
                const Panel(child: SizedBox(height: 200, child: EmptyState(icon: Icons.insights_outlined, title: 'No evaluation results yet', hint: 'Run `make eval` in the backend, then refresh this page.')))
              else ...[
                _summary(cur),
                const SizedBox(height: K.s16),
                _fields(cur),
              ],
              const SizedBox(height: K.s16),
              LayoutBuilder(builder: (c, box) {
                final p = _providers(q.providers), m = _prompts(q.prompts);
                return box.maxWidth >= 1000
                    ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(child: p), const SizedBox(width: K.s16), Expanded(child: m)])
                    : Column(children: [p, const SizedBox(height: K.s16), m]);
              }),
            ]),
          );
        },
      );

  Widget _summary(Map cur) {
    final s = cur['summary'] as Map;
    return MetricStrip([
      Metric('Precision', pct(s['precision']), sub: '${s['truePositives']} TP · ${s['falsePositives']} FP'),
      Metric('Recall', pct(s['recall']), sub: '${s['falseNegatives']} missed'),
      Metric('F1 (macro)', pct(s['macroF1']), sub: 'over ${(cur['fields'] as List).length} fields'),
      Metric('Abstention', pct(s['abstentionRate']), sub: 'recall ${pct(s['abstentionRecall'])}'),
      Metric('Documents', '${s['documents']}', sub: '${cur['provider']['model']}'),
    ]);
  }

  Widget _fields(Map cur) {
    final fields = (cur['fields'] as List).cast<Map>();
    Widget cell(num? v) => Text(v == null ? '—' : v.toStringAsFixed(2), textAlign: TextAlign.right, style: numStyle.copyWith(color: v != null && v < .8 ? K.badInk : K.ink));
    return Panel(
      title: 'Per field · ${cur['provider']['name']} · ${cur['prompt']['version']}',
      padding: EdgeInsets.zero,
      child: Column(children: [
        const TableHead([('Field', 5, false), ('Support', 2, true), ('Precision', 2, true), ('Recall', 2, true), ('F1', 2, true), ('Abstain', 2, true), ('Mean conf.', 2, true)]),
        for (final f in fields)
          DataRow2(
            height: 40,
            flex: const [5, 2, 2, 2, 2, 2, 2],
            cells: [
              Text('${f['label']}', style: K.body.copyWith(fontSize: 13), overflow: TextOverflow.ellipsis),
              Text('${f['support']}', textAlign: TextAlign.right, style: K.mono),
              cell(f['precision']),
              cell(f['recall']),
              cell(f['f1']),
              Text('${f['abstentions']}', textAlign: TextAlign.right, style: K.mono),
              Text(f['meanConfidence'] == null ? '—' : (f['meanConfidence'] as num).toStringAsFixed(2), textAlign: TextAlign.right, style: K.mono),
            ],
          ),
      ]),
    );
  }

  Widget _providers(List ps) => Panel(
        title: 'Model registry',
        padding: EdgeInsets.zero,
        child: Column(children: [
          const TableHead([('Provider', 2, false), ('Model', 4, false), ('Status', 3, false)]),
          for (final p in ps)
            DataRow2(
              height: 48,
              flex: const [2, 4, 3],
              cells: [
                Text('${p['name']}', style: K.body.copyWith(fontSize: 13, fontWeight: FontWeight.w500)),
                Text('${p['model']}', style: K.mono, overflow: TextOverflow.ellipsis),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Tooltip(
                    message: '${p['reason']}',
                    child: p['paid'] == true
                        ? const Pill('Paid · gated', tone: Tone.muted, icon: Icons.lock_outline)
                        : p['available'] == true
                            ? const Pill('Available · local', tone: Tone.info, icon: Icons.check)
                            : const Pill('Unavailable', tone: Tone.bad, icon: Icons.block),
                  ),
                ),
              ],
            ),
        ]),
      );

  Widget _prompts(List ps) => Panel(
        title: 'Prompt registry',
        padding: EdgeInsets.zero,
        child: Column(children: [
          const TableHead([('Version', 3, false), ('SHA-256', 4, false), ('', 2, true)]),
          for (final p in ps.reversed)
            DataRow2(
              height: 40,
              flex: const [3, 4, 2],
              cells: [
                Text('${p['version']}', style: K.body.copyWith(fontSize: 13, fontWeight: FontWeight.w500)),
                Text(short('${p['sha256']}', 8), style: K.mono),
                Align(alignment: Alignment.centerRight, child: p['active'] == true ? const Pill('Active', tone: Tone.info) : const SizedBox()),
              ],
            ),
        ]),
      );
}
