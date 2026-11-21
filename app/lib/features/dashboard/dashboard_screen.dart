import 'package:flutter/material.dart';
import '../../data/app_state.dart';
import '../../models/models.dart';
import '../../theme/tokens.dart';
import '../../ui/widgets.dart';

/// UI-001 study dashboard.
class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final d = AppScope.of(context).dashboard;
    final main = Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      if (d.studies.isEmpty)
        const Panel(child: SizedBox(height: 200, child: EmptyState(icon: Icons.science_outlined, title: 'No studies yet', hint: 'Studies appear here once a protocol is configured.')))
      else
        for (final s in d.studies) ...[_StudyPanel(s, [for (final x in d.sites) if (x.studyId == s.id) x]), const SizedBox(height: K.s16)],
    ]);
    final rail = Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      _Alerts(d.alerts),
      const SizedBox(height: K.s16),
      _Tasks(d.tasks),
      const SizedBox(height: K.s16),
      _Milestones(d.milestones),
    ]);
    return LayoutBuilder(builder: (context, box) {
      final two = box.maxWidth >= 1100;
      return ListView(padding: EdgeInsets.fromLTRB(K.s32, 28, K.s32, K.s48), children: [
        PageHeader(
          title: 'Research dashboard',
          subtitle: '${d.studies.length} ${d.studies.length == 1 ? 'study' : 'studies'} · ${d.sites.length} sites · '
              '${d.alerts.where((a) => a.severity == 'critical').length} critical alerts',
        ),
        const SizedBox(height: K.s24),
        if (two)
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Expanded(flex: 62, child: main),
            const SizedBox(width: K.s24),
            Expanded(flex: 38, child: rail),
          ])
        else ...[main, rail],
      ]);
    });
  }
}

class _Metric extends StatelessWidget {
  final String label, value, of;
  final double fraction;
  final Color color;
  const _Metric(this.label, this.value, this.of, this.fraction, {this.color = K.accent});
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label.toUpperCase(), style: K.label),
        const SizedBox(height: 6),
        Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Text(value, style: K.title),
          if (of.isNotEmpty) Text(' $of', style: K.small),
        ]),
        const SizedBox(height: 8),
        Bar(fraction, color: color),
      ]);
}

class _StudyPanel extends StatelessWidget {
  final Study s;
  final List<Site> sites;
  const _StudyPanel(this.s, this.sites);

  @override
  Widget build(BuildContext context) {
    final rec = s.target == 0 ? 0.0 : s.enrolled / s.target;
    return Panel(
      padding: EdgeInsets.zero,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Padding(
          padding: const EdgeInsets.all(K.s24),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(child: Text(s.title, style: K.title)),
              const SizedBox(width: 12),
              Pill('Phase ${s.phase}', tone: Tone.info),
            ]),
            const SizedBox(height: 2),
            Text(s.id, style: K.mono),
            const SizedBox(height: K.s24),
            Row(children: [
              Expanded(child: _Metric('Recruitment', '${s.enrolled}', 'of ${s.target} participants', rec)),
              const SizedBox(width: K.s32),
              Expanded(child: _Metric('eCRF completeness', '${(s.completeness * 100).round()}%', '', s.completeness, color: K.okLine)),
            ]),
          ]),
        ),
        if (sites.isNotEmpty) ...[
          const Divider(),
          Padding(
            padding: const EdgeInsets.fromLTRB(K.s24, 14, K.s24, 4),
            child: Row(children: [
              const Expanded(flex: 4, child: Text('SITE', style: K.label)),
              const Expanded(flex: 4, child: Text('ENROLMENT', style: K.label)),
              Expanded(flex: 2, child: Text('OPEN QUERIES', style: K.label, textAlign: TextAlign.right)),
            ]),
          ),
          for (final x in sites)
            Padding(
              padding: const EdgeInsets.fromLTRB(K.s24, 10, K.s24, 10),
              child: Row(children: [
                Expanded(flex: 4, child: Text(x.name, style: K.body.copyWith(fontWeight: FontWeight.w500), overflow: TextOverflow.ellipsis)),
                Expanded(
                  flex: 4,
                  child: Row(children: [
                    Expanded(child: Bar(x.target == 0 ? 0 : x.enrolled / x.target, height: 5)),
                    const SizedBox(width: 10),
                    SizedBox(width: 48, child: Text('${x.enrolled}/${x.target}', style: K.small)),
                  ]),
                ),
                Expanded(
                  flex: 2,
                  child: Align(alignment: Alignment.centerRight, child: x.openQueries == 0 ? const Text('0', style: K.small) : Pill('${x.openQueries}', tone: Tone.ai)),
                ),
              ]),
            ),
          const SizedBox(height: 8),
        ],
      ]),
    );
  }
}

class _Alerts extends StatelessWidget {
  final List<Alert> alerts;
  const _Alerts(this.alerts);
  @override
  Widget build(BuildContext context) => Panel(
        title: 'Alerts',
        padding: EdgeInsets.zero,
        child: alerts.isEmpty
            ? const SizedBox(height: 120, child: EmptyState(icon: Icons.check_circle_outline, title: 'All clear', hint: 'No alerts need attention.'))
            : Column(children: [
                for (var i = 0; i < alerts.length; i++) ...[
                  if (i > 0) const Divider(),
                  Padding(
                    padding: const EdgeInsets.all(K.s16),
                    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      _SevIcon(alerts[i].severity),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text(alerts[i].message, style: K.body.copyWith(fontSize: 13.5)),
                          const SizedBox(height: 2),
                          Text(alerts[i].studyId, style: K.mono),
                        ]),
                      ),
                    ]),
                  ),
                ],
              ]),
      );
}

class _SevIcon extends StatelessWidget {
  final String sev;
  const _SevIcon(this.sev);
  @override
  Widget build(BuildContext context) {
    final (tone, icon) = switch (sev) {
      'critical' => (Tone.bad, Icons.priority_high),
      'warning' => (Tone.ai, Icons.warning_amber_rounded),
      _ => (Tone.info, Icons.info_outline),
    };
    final (bg, _, ink) = toneColors(tone);
    return Tooltip(
      message: sev,
      child: Container(width: 28, height: 28, decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(8)), child: Icon(icon, size: 16, color: ink)),
    );
  }
}

class _Tasks extends StatelessWidget {
  final List<StudyTask> tasks;
  const _Tasks(this.tasks);
  @override
  Widget build(BuildContext context) => Panel(
        title: 'My tasks',
        padding: EdgeInsets.zero,
        child: tasks.isEmpty
            ? const SizedBox(height: 120, child: EmptyState(icon: Icons.task_alt, title: 'Nothing due', hint: 'Assigned tasks show up here.'))
            : Column(children: [
                for (var i = 0; i < tasks.length; i++) ...[
                  if (i > 0) const Divider(),
                  InkWell(
                    onTap: tasks[i].participantId == null ? null : () => Navigator.of(context).pushNamed('/participant/${tasks[i].participantId}'),
                    child: Padding(
                      padding: const EdgeInsets.all(K.s16),
                      child: Row(children: [
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(tasks[i].title, style: K.body.copyWith(fontWeight: FontWeight.w500, fontSize: 13.5)),
                            const SizedBox(height: 2),
                            Text('${tasks[i].assignee} · due ${tasks[i].due}${tasks[i].participantId == null ? '' : ' · ${tasks[i].participantId}'}', style: K.small),
                          ]),
                        ),
                        if (tasks[i].participantId != null) const Icon(Icons.chevron_right, size: 18, color: K.ink3),
                      ]),
                    ),
                  ),
                ],
              ]),
      );
}

class _Milestones extends StatelessWidget {
  final List<Milestone> ms;
  const _Milestones(this.ms);
  @override
  Widget build(BuildContext context) => Panel(
        title: 'Milestones',
        child: ms.isEmpty
            ? const SizedBox(height: 100, child: EmptyState(icon: Icons.flag_outlined, title: 'No milestones', hint: 'Milestones for your studies appear here.'))
            : Column(children: [
                for (var i = 0; i < ms.length; i++)
                  IntrinsicHeight(
                    child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                      SizedBox(
                        width: 20,
                        child: Column(children: [
                          Container(
                            width: 12,
                            height: 12,
                            margin: const EdgeInsets.only(top: 4),
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: ms[i].done ? K.okLine : K.surface,
                              border: Border.all(color: ms[i].done ? K.okLine : K.lineStrong, width: 2),
                            ),
                          ),
                          if (i < ms.length - 1) Expanded(child: Container(width: 2, color: K.line)),
                        ]),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Padding(
                          padding: const EdgeInsets.only(bottom: 14),
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(ms[i].name, style: K.body.copyWith(fontWeight: FontWeight.w500, fontSize: 13.5, color: ms[i].done ? K.ink2 : K.ink)),
                            Text('${ms[i].date} · ${ms[i].studyId}${ms[i].done ? ' · done' : ''}', style: K.small),
                          ]),
                        ),
                      ),
                    ]),
                  ),
              ]),
      );
}
