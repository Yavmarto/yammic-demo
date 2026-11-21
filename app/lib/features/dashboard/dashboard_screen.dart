import 'package:flutter/material.dart';
import 'package:zeta_flutter/zeta_flutter.dart';
import '../../data/app_state.dart';

/// UI-001 study dashboard (thin).
class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final d = AppScope.of(context).dashboard;
    final t = Theme.of(context).textTheme;
    Widget h(String s) => Padding(
        padding: const EdgeInsets.only(top: 24, bottom: 8), child: Text(s, style: t.titleMedium));
    return ListView(padding: const EdgeInsets.all(24), children: [
      Text('Research dashboard', style: t.headlineSmall),
      h('Studies'),
      Wrap(spacing: 16, runSpacing: 16, children: [
        for (final s in d.studies)
          SizedBox(
            width: 340,
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(s.title, style: t.titleSmall),
                  Text('${s.id} · phase ${s.phase}'),
                  const SizedBox(height: 12),
                  Text('Recruitment ${s.enrolled}/${s.target}'),
                  LinearProgressIndicator(value: s.target == 0 ? 0 : s.enrolled / s.target),
                  const SizedBox(height: 8),
                  Text('eCRF completeness ${(s.completeness * 100).round()}%'),
                  LinearProgressIndicator(value: s.completeness),
                ]),
              ),
            ),
          ),
      ]),
      h('Alerts'),
      for (final a in d.alerts)
        ListTile(
          leading: Icon(
            a.severity == 'critical' ? Icons.error : a.severity == 'warning' ? Icons.warning_amber : Icons.info_outline,
            color: a.severity == 'critical' ? Zeta.of(context).colors.mainNegative : a.severity == 'warning' ? Zeta.of(context).colors.mainWarning : null,
          ),
          title: Text(a.message),
          subtitle: Text(a.studyId),
        ),
      h('Sites'),
      Card(
        child: Column(children: [
          for (final s in d.sites)
            ListTile(
              title: Text(s.name),
              subtitle: Text('${s.studyId} · enrolled ${s.enrolled}/${s.target}'),
              trailing: Text('${s.openQueries} open queries'),
            ),
        ]),
      ),
      h('Tasks'),
      Card(
        child: Column(children: [
          for (final k in d.tasks)
            ListTile(
              title: Text(k.title),
              subtitle: Text('${k.assignee} · due ${k.due}${k.participantId == null ? '' : ' · ${k.participantId}'}'),
              onTap: k.participantId == null
                  ? null
                  : () => Navigator.of(context).pushNamed('/participant/${k.participantId}'),
            ),
        ]),
      ),
      h('Milestones'),
      Card(
        child: Column(children: [
          for (final m in d.milestones)
            ListTile(
              leading: Icon(m.done ? Icons.check_circle : Icons.flag_outlined),
              title: Text(m.name),
              subtitle: Text('${m.studyId} · ${m.date}'),
            ),
        ]),
      ),
    ]);
  }
}
