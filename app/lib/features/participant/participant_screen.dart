import 'package:flutter/material.dart';
import 'package:zeta_flutter/zeta_flutter.dart';
import '../../data/app_state.dart';
import '../../models/models.dart';

/// Participant list at /participants.
class ParticipantListScreen extends StatelessWidget {
  const ParticipantListScreen({super.key});
  @override
  Widget build(BuildContext context) {
    final ps = AppScope.of(context).participants;
    return ListView(padding: const EdgeInsets.all(24), children: [
      Text('Participants', style: Theme.of(context).textTheme.headlineSmall),
      const SizedBox(height: 12),
      Card(
        child: Column(children: [
          for (final p in ps)
            ListTile(
              title: Text(p.id),
              subtitle: Text('${p.studyId} · ${p.siteId} · ${p.age}${p.sex}'),
              trailing: Chip(label: Text(p.status)),
              onTap: () => Navigator.of(context).pushNamed('/participant/${p.id}'),
            ),
        ]),
      ),
    ]);
  }
}

/// UI-002 participant workspace.
class ParticipantScreen extends StatelessWidget {
  final String id;
  const ParticipantScreen({super.key, required this.id});

  @override
  Widget build(BuildContext context) {
    final p = AppScope.of(context).participant(id);
    if (p == null) return Center(child: Text('Unknown participant $id'));
    final t = Theme.of(context).textTheme;
    Widget h(String s) => Padding(
        padding: const EdgeInsets.only(top: 24, bottom: 8), child: Text(s, style: t.titleMedium));
    final waiting = p.ecrfs.any((e) => e.status == 'awaiting_review');
    return ListView(padding: const EdgeInsets.all(24), children: [
      Row(children: [
        Text(p.id, style: t.headlineSmall),
        const SizedBox(width: 12),
        Chip(label: Text(p.status)),
        const Spacer(),
        FilledButton.icon(
          icon: const Icon(Icons.fact_check_outlined),
          label: Text(waiting ? 'Review AI values' : 'Open AI review'),
          onPressed: () => Navigator.of(context).pushNamed('/review', arguments: p.id),
        ),
      ]),
      Text('${p.studyId} · ${p.siteId} · ${p.age} y · ${p.sex}'),
      h('Clinical summary'),
      Card(child: Padding(padding: const EdgeInsets.all(16), child: Text(p.summary))),
      h('Visit timeline'),
      Card(
        child: Column(children: [
          for (final v in p.visits)
            ListTile(
              leading: Icon(switch (v.status) {
                'completed' => Icons.check_circle,
                'missed' => Icons.cancel,
                _ => Icons.schedule,
              }),
              title: Text(v.name),
              subtitle: Text('${v.date} · ${v.status}${v.note.isEmpty ? '' : ' · ${v.note}'}'),
            ),
          if (p.visits.isEmpty) const ListTile(title: Text('No visits')),
        ]),
      ),
      h('eCRF status'),
      Card(
        child: Column(children: [
          for (final e in p.ecrfs)
            ListTile(
              title: Text(e.form),
              subtitle: LinearProgressIndicator(value: e.completePct / 100),
              trailing: Text(e.status.replaceAll('_', ' ')),
            ),
          if (p.ecrfs.isEmpty) const ListTile(title: Text('No eCRFs')),
        ]),
      ),
      h('Quality issues'),
      Card(
        child: Column(children: [
          for (final q in p.issues) _issue(context, q),
          if (p.issues.isEmpty) const ListTile(title: Text('None')),
        ]),
      ),
      h('Treatment history'),
      Card(
        child: Column(children: [
          for (final r in p.treatments)
            ListTile(
              title: Text('${r.name} ${r.dose}'),
              subtitle: Text('${r.start} → ${r.end ?? 'ongoing'}'),
            ),
          if (p.treatments.isEmpty) const ListTile(title: Text('None')),
        ]),
      ),
    ]);
  }

  Widget _issue(BuildContext context, QualityIssue q) => ListTile(
        leading: Icon(Icons.report_problem_outlined,
            color: q.severity == 'high' ? Zeta.of(context).colors.mainNegative : q.severity == 'medium' ? Zeta.of(context).colors.mainWarning : null),
        title: Text(q.message),
        subtitle: Text(q.field),
      );
}
