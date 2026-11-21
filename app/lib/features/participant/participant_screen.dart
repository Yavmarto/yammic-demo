import 'package:flutter/material.dart';
import '../../data/app_state.dart';
import '../../models/models.dart';
import '../../theme/tokens.dart';
import '../../ui/widgets.dart';

String _nice(String s) => s.isEmpty ? s : s[0].toUpperCase() + s.substring(1).replaceAll('_', ' ');

/// Participant list at /participants.
class ParticipantListScreen extends StatelessWidget {
  const ParticipantListScreen({super.key});
  @override
  Widget build(BuildContext context) {
    final ps = AppScope.of(context).participants;
    return ListView(padding: const EdgeInsets.fromLTRB(K.s32, 28, K.s32, K.s48), children: [
      PageHeader(title: 'Participants', subtitle: '${ps.length} pseudonymised participants'),
      const SizedBox(height: K.s24),
      if (ps.isEmpty)
        const Panel(child: SizedBox(height: 220, child: EmptyState(icon: Icons.people_outline, title: 'No participants yet', hint: 'Participants appear once screening starts.')))
      else
        Panel(
          padding: EdgeInsets.zero,
          child: Column(children: [
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: K.s16, vertical: 12),
              child: Row(children: [
                Expanded(flex: 3, child: Text('PARTICIPANT', style: K.label)),
                Expanded(flex: 3, child: Text('STUDY · SITE', style: K.label)),
                Expanded(flex: 2, child: Text('AGE · SEX', style: K.label)),
                Expanded(flex: 2, child: Text('STATUS', style: K.label)),
                Expanded(flex: 3, child: Text('NEEDS ATTENTION', style: K.label)),
                SizedBox(width: 24),
              ]),
            ),
            for (final p in ps) ...[const Divider(), _Row(p)],
          ]),
        ),
    ]);
  }
}

class _Row extends StatefulWidget {
  final Participant p;
  const _Row(this.p);
  @override
  State<_Row> createState() => _RowState();
}

class _RowState extends State<_Row> {
  bool hover = false;
  @override
  Widget build(BuildContext context) {
    final p = widget.p;
    final waiting = p.ecrfs.where((e) => e.status == 'awaiting_review').length;
    return MouseRegion(
      onEnter: (_) => setState(() => hover = true),
      onExit: (_) => setState(() => hover = false),
      child: InkWell(
        onTap: () => Navigator.of(context).pushNamed('/participant/${p.id}'),
        child: AnimatedContainer(
          duration: K.fast,
          color: hover ? K.bg : Colors.transparent,
          padding: const EdgeInsets.symmetric(horizontal: K.s16, vertical: 14),
          child: Row(children: [
            Expanded(flex: 3, child: Text(p.id, style: K.body.copyWith(fontWeight: FontWeight.w600))),
            Expanded(flex: 3, child: Text('${p.studyId} · ${p.siteId}', style: K.small, overflow: TextOverflow.ellipsis)),
            Expanded(flex: 2, child: Text('${p.age} ${p.sex}', style: K.small)),
            Expanded(flex: 2, child: Align(alignment: Alignment.centerLeft, child: Pill(_nice(p.status), tone: statusTone(p.status)))),
            Expanded(
              flex: 3,
              child: Wrap(spacing: 6, runSpacing: 4, children: [
                if (waiting > 0) Pill('$waiting to review', tone: Tone.ai, icon: Icons.auto_awesome),
                if (p.issues.isNotEmpty) Pill('${p.issues.length} ${p.issues.length == 1 ? 'issue' : 'issues'}', tone: Tone.bad),
                if (waiting == 0 && p.issues.isEmpty) const Text('None', style: K.small),
              ]),
            ),
            const SizedBox(width: 24, child: Icon(Icons.chevron_right, size: 18, color: K.ink3)),
          ]),
        ),
      ),
    );
  }
}

/// UI-002 participant workspace.
class ParticipantScreen extends StatelessWidget {
  final String id;
  const ParticipantScreen({super.key, required this.id});

  @override
  Widget build(BuildContext context) {
    final p = AppScope.of(context).participant(id);
    if (p == null) {
      return EmptyState(
        icon: Icons.person_search_outlined,
        title: 'Unknown participant $id',
        hint: 'This participant is not in the current study data.',
        action: OutlinedButton(onPressed: () => Navigator.of(context).pushReplacementNamed('/participants'), child: const Text('Back to participants')),
      );
    }
    final waiting = p.ecrfs.any((e) => e.status == 'awaiting_review');
    final left = Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Panel(title: 'Clinical summary', child: Text(p.summary.isEmpty ? 'No summary recorded.' : p.summary, style: K.body.copyWith(height: 1.6))),
      const SizedBox(height: K.s16),
      Panel(title: 'Visit timeline', child: _Visits(p.visits)),
      const SizedBox(height: K.s16),
      Panel(title: 'Treatment history', padding: EdgeInsets.zero, child: _Treatments(p.treatments)),
    ]);
    final right = Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Panel(title: 'eCRF status', padding: EdgeInsets.zero, child: _Ecrfs(p.ecrfs)),
      const SizedBox(height: K.s16),
      Panel(title: 'Quality issues', padding: EdgeInsets.zero, child: _Issues(p.issues)),
    ]);
    return LayoutBuilder(builder: (context, box) {
      final two = box.maxWidth >= 1000;
      return ListView(padding: const EdgeInsets.fromLTRB(K.s32, 28, K.s32, K.s48), children: [
        PageHeader(
          crumbs: const [('Participants', '/participants'), ('Workspace', null)],
          title: p.id,
          subtitle: '${p.studyId} · ${p.siteId} · ${p.age} y · ${p.sex}',
          trailing: Row(mainAxisSize: MainAxisSize.min, children: [
            Pill(_nice(p.status), tone: statusTone(p.status)),
            const SizedBox(width: K.s16),
            FilledButton.icon(
              icon: const Icon(Icons.auto_awesome, size: 18),
              label: Text(waiting ? 'Review AI values' : 'Open AI review'),
              onPressed: () => Navigator.of(context).pushNamed('/review', arguments: p.id),
            ),
          ]),
        ),
        const SizedBox(height: K.s24),
        if (two)
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Expanded(flex: 58, child: left),
            const SizedBox(width: K.s24),
            Expanded(flex: 42, child: right),
          ])
        else ...[left, const SizedBox(height: K.s16), right],
      ]);
    });
  }
}

class _Visits extends StatelessWidget {
  final List<Visit> vs;
  const _Visits(this.vs);
  @override
  Widget build(BuildContext context) {
    if (vs.isEmpty) return const Text('No visits scheduled yet.', style: K.small);
    return Column(children: [
      for (var i = 0; i < vs.length; i++)
        IntrinsicHeight(
          child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            SizedBox(
              width: 22,
              child: Column(children: [
                Container(
                  width: 14,
                  height: 14,
                  margin: const EdgeInsets.only(top: 3),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: switch (vs[i].status) { 'completed' => K.okLine, 'missed' => K.badLine, _ => K.surface },
                    border: Border.all(color: switch (vs[i].status) { 'completed' => K.okLine, 'missed' => K.badLine, _ => K.lineStrong }, width: 2),
                  ),
                  child: vs[i].status == 'scheduled' ? null : Icon(vs[i].status == 'missed' ? Icons.close : Icons.check, size: 9, color: Colors.white),
                ),
                if (i < vs.length - 1) Expanded(child: Container(width: 2, color: K.line)),
              ]),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Text(vs[i].name, style: K.body.copyWith(fontWeight: FontWeight.w600)),
                    const SizedBox(width: 8),
                    Text(vs[i].date, style: K.mono),
                  ]),
                  Text('${_nice(vs[i].status)}${vs[i].note.isEmpty ? '' : ' · ${vs[i].note}'}', style: K.small),
                ]),
              ),
            ),
          ]),
        ),
    ]);
  }
}

class _Treatments extends StatelessWidget {
  final List<Treatment> ts;
  const _Treatments(this.ts);
  @override
  Widget build(BuildContext context) => ts.isEmpty
      ? const Padding(padding: EdgeInsets.all(K.s16), child: Text('No treatments recorded.', style: K.small))
      : Column(children: [
          for (var i = 0; i < ts.length; i++) ...[
            if (i > 0) const Divider(),
            Padding(
              padding: const EdgeInsets.all(K.s16),
              child: Row(children: [
                Expanded(child: Text('${ts[i].name} ${ts[i].dose}'.trim(), style: K.body.copyWith(fontWeight: FontWeight.w500))),
                Text('${ts[i].start} → ${ts[i].end ?? 'ongoing'}', style: K.mono),
              ]),
            ),
          ],
        ]);
}

class _Ecrfs extends StatelessWidget {
  final List<Ecrf> es;
  const _Ecrfs(this.es);
  @override
  Widget build(BuildContext context) => es.isEmpty
      ? const Padding(padding: EdgeInsets.all(K.s16), child: Text('No eCRFs started.', style: K.small))
      : Column(children: [
          for (var i = 0; i < es.length; i++) ...[
            if (i > 0) const Divider(),
            Padding(
              padding: const EdgeInsets.all(K.s16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Expanded(child: Text(es[i].form, style: K.body.copyWith(fontWeight: FontWeight.w500))),
                  Pill(_nice(es[i].status), tone: statusTone(es[i].status), icon: es[i].status == 'awaiting_review' ? Icons.auto_awesome : null),
                ]),
                const SizedBox(height: 10),
                Row(children: [
                  Expanded(child: Bar(es[i].completePct / 100, color: es[i].status == 'complete' ? K.okLine : K.accent, height: 5)),
                  const SizedBox(width: 10),
                  SizedBox(width: 36, child: Text('${es[i].completePct}%', style: K.small, textAlign: TextAlign.right)),
                ]),
              ]),
            ),
          ],
        ]);
}

class _Issues extends StatelessWidget {
  final List<QualityIssue> qs;
  const _Issues(this.qs);
  @override
  Widget build(BuildContext context) => qs.isEmpty
      ? const SizedBox(height: 120, child: EmptyState(icon: Icons.verified_outlined, title: 'No quality issues', hint: 'Data checks found nothing to fix.'))
      : Column(children: [
          for (var i = 0; i < qs.length; i++) ...[
            if (i > 0) const Divider(),
            Padding(
              padding: const EdgeInsets.all(K.s16),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Pill(_nice(qs[i].severity), tone: switch (qs[i].severity) { 'high' => Tone.bad, 'medium' => Tone.ai, _ => Tone.muted }),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(qs[i].message, style: K.body.copyWith(fontSize: 13.5)),
                    if (qs[i].field.isNotEmpty) Text(qs[i].field, style: K.mono),
                  ]),
                ),
              ]),
            ),
          ],
        ]);
}
