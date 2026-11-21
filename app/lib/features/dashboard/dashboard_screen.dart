import 'package:flutter/material.dart';
import '../../data/session.dart';
import '../../theme/tokens.dart';
import '../../ui/async.dart';
import '../../ui/format.dart';
import '../../ui/widgets.dart';

const studyId = 'GBM-NL-2026-01';

class _Data {
  final Map dash;
  final List participants, pendingTop, activity;
  _Data(this.dash, this.participants, this.pendingTop, this.activity);
}

Future<_Data> _load(Session s) => s.run((a) async {
      final dash = await a.get('/studies/$studyId/dashboard') as Map;
      final parts = await a.get('/participants') as List;
      final top = <Map>[];
      for (final p in parts.where((p) => (p['extractionsPending'] as int) > 0)) {
        for (final e in await a.get('/participants/${p['id']}/extractions') as List) {
          if (e['reviewState'] == 'pending') top.add(e);
        }
      }
      // proposals first (lowest confidence first), abstentions after: those cannot be accepted anyway
      top.sort((x, y) {
        final a = x['status'] == 'abstained' ? 1 : 0, b = y['status'] == 'abstained' ? 1 : 0;
        return a != b ? a - b : (x['confidence'] as num).compareTo(y['confidence'] as num);
      });
      final act = await a.get('/audit', query: {'limit': '4'});
      s.setPending((dash['kpis'] as Map)['extractionsPending'] as int);
      return _Data(dash, parts, top, (act['items'] as List));
    });

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});
  @override
  Widget build(BuildContext context) => Loader<_Data>(
        load: _load,
        builder: (c, d, reload) => _Body(d, reload),
      );
}

class _Body extends StatelessWidget {
  final _Data d;
  final VoidCallback reload;
  const _Body(this.d, this.reload);

  Map get k => d.dash['kpis'];
  void go(BuildContext c, String r, [Object? a]) => Navigator.of(c).pushReplacementNamed(r, arguments: a);

  @override
  Widget build(BuildContext context) {
    final pending = k['extractionsPending'] as int;
    final enrolled = k['enrolled'] as int, target = k['target'] as int;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(K.s24),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 1440),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          PageHeader(
            title: 'Research dashboard',
            subtitle: '${d.dash['title']} · Phase ${d.dash['phase']} · ${(d.dash['sites'] as List).length} sites',
            trailing: OutlinedButton.icon(onPressed: reload, icon: const Icon(Icons.refresh, size: 18), label: const Text('Refresh')),
          ),
          const SizedBox(height: K.s16),
          MetricStrip([
            Metric('Enrolled', '$enrolled/$target', sub: 'of target', progress: enrolled / target),
            Metric('eCRF verified', pct(k['ecrfCompleteness']), sub: (k['ecrfFieldsTotal'] as int) == 0 ? 'verified values only' : '${k['ecrfFieldsVerified']} of ${k['ecrfFieldsTotal']} fields · verified only'),
            Metric('Open queries', '${k['openQueries']}', sub: '${k['sdvDone']} SDV done · ${k['sdvPending']} pending'),
            Metric('AI queue', '$pending', dot: K.aiLine, sub: '${k['needsAttention']} need attention', onTap: () => go(context, '/review')),
            Metric('AI acceptance', k['aiAcceptanceRate'] == null ? '—' : pct(k['aiAcceptanceRate']), sub: '${k['extractionsReviewed']} of ${k['extractionsTotal']} reviewed'),
          ]),
          const SizedBox(height: K.s32),
          LayoutBuilder(builder: (c, box) {
            final two = box.maxWidth >= 1000;
            final left = Column(children: [
              _recruitment(),
              const SizedBox(height: K.s16),
              _sites(context),
            ]);
            final right = Column(children: [
              _queue(context, pending),
              const SizedBox(height: K.s16),
              _alerts(),
            ]);
            return two
                ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(flex: 8, child: left), const SizedBox(width: K.s16), Expanded(flex: 4, child: right)])
                : Column(children: [left, const SizedBox(height: K.s16), right]);
          }),
          const SizedBox(height: K.s16),
          LayoutBuilder(builder: (c, box) {
            final two = box.maxWidth >= 1000;
            final t = _tasks(context), a = _activity(context);
            return two
                ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(flex: 7, child: t), const SizedBox(width: K.s16), Expanded(flex: 5, child: a)])
                : Column(children: [t, const SizedBox(height: K.s16), a]);
          }),
        ]),
      ),
    );
  }

  /// Monthly enrolment from participants' enrolled dates (real data, FHIR-synced).
  Widget _recruitment() {
    final target = k['target'] as int;
    final dates = [for (final p in d.participants) if (p['enrolledDate'] != null) DateTime.parse(p['enrolledDate'])]..sort();
    final months = <String, int>{};
    if (dates.isNotEmpty) {
      var m = DateTime(dates.first.year, dates.first.month);
      final end = DateTime(Session.demoToday.year, Session.demoToday.month);
      while (!m.isAfter(end)) {
        months['${m.year}-${m.month}'] = 0;
        m = DateTime(m.year, m.month + 1);
      }
      for (final x in dates) {
        months['${x.year}-${x.month}'] = months['${x.year}-${x.month}']! + 1;
      }
    }
    final labels = [for (final key in months.keys) fmtDate('${key.split('-')[0]}-${key.split('-')[1].padLeft(2, '0')}-01').substring(2, 6)];
    return Panel(
      title: 'Recruitment',
      trailing: Row(mainAxisSize: MainAxisSize.min, children: [
        _legend(K.accent.withValues(alpha: .25), 'New per month'),
        const SizedBox(width: 12),
        _legend(K.accent, 'Cumulative'),
        const SizedBox(width: 12),
        _legend(K.chart3, 'Target $target'),
      ]),
      child: months.isEmpty
          ? const SizedBox(height: 200, child: EmptyState(icon: Icons.show_chart, title: 'No recruitment data yet', hint: 'Sync the FHIR connection to load participants.'))
          : SizedBox(
              height: 200,
              child: Semantics(
                label: 'Recruitment chart: ${dates.length} of $target enrolled',
                child: CustomPaint(painter: RecruitmentPainter(months.values.toList(), labels, target), size: Size.infinite),
              ),
            ),
    );
  }

  Widget _legend(Color c, String t) => Row(mainAxisSize: MainAxisSize.min, children: [
        Container(width: 12, height: 3, color: c),
        const SizedBox(width: 6),
        Text(t, style: K.small.copyWith(fontSize: 11.5)),
      ]);

  Widget _sites(BuildContext context) {
    final sites = d.dash['sites'] as List;
    final flex = [4, 2, 2, 3];
    return Panel(
      title: 'Site performance',
      padding: EdgeInsets.zero,
      child: Column(children: [
        const TableHead([('Site', 4, false), ('Enrolled', 2, true), ('Queries', 2, true), ('Enrolment', 3, false)]),
        for (final s in sites)
          DataRow2(
            flex: flex,
            cells: [
              Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
                Text('${s['shortName'] ?? s['name']}', style: K.body.copyWith(fontWeight: FontWeight.w500), overflow: TextOverflow.ellipsis),
                Text('${s['city'] != null ? '${s['city']} · ' : ''}${s['id']}', style: K.small.copyWith(fontSize: 11.5, color: K.ink3)),
              ]),
              Text('${s['enrolled']}/${s['targetEnrolment'] ?? '—'}', textAlign: TextAlign.right, style: numStyle),
              Text('${s['openQueries']}', textAlign: TextAlign.right, style: numStyle),
              Padding(
                padding: const EdgeInsets.only(left: K.s16),
                child: Bar(((s['targetEnrolment'] ?? 0) == 0) ? 0 : (s['enrolled'] as int) / (s['targetEnrolment'] as int), height: 6),
              ),
            ],
          ),
        Padding(
          padding: const EdgeInsets.all(K.s12),
          child: Text('${sites.length} sites · ${k['enrolled']} enrolled · ${k['openQueries']} open queries', style: K.small.copyWith(fontSize: 12, color: K.ink3)),
        ),
      ]),
    );
  }

  Widget _queue(BuildContext context, int pending) {
    final top = d.pendingTop.take(3).toList();
    final total = (k['extractionsTotal'] as int).clamp(1, 1 << 30);
    return Panel(
      title: 'AI review',
      trailing: LinkText('$pending pending · Review →', () => go(context, '/review')),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(2),
          child: SizedBox(
            height: 4,
            child: Row(children: [
              for (final (n, c) in [
                (pending, K.aiLine),
                ((k['extractionsAccepted'] as int) + (k['extractionsCorrected'] as int), K.okLine),
                (k['extractionsRejected'] as int, K.badLine),
                (k['extractionsDeferred'] as int, K.mutedLine),
              ])
                if (n > 0) Expanded(flex: n * 1000 ~/ total, child: Container(color: c)),
            ]),
          ),
        ),
        const SizedBox(height: 4),
        Text('Lowest confidence first', style: K.small.copyWith(fontSize: 11.5)),
        if (top.isEmpty)
          const Padding(padding: EdgeInsets.symmetric(vertical: K.s16), child: Text('Queue clear. All values reviewed.', style: K.small))
        else
          for (final e in top)
            InkWell(
              onTap: () => go(context, '/review', e['participantId']),
              child: SizedBox(
                height: 44,
                child: Row(children: [
                  Icon(e['status'] == 'abstained' ? Icons.help_outline : Icons.auto_awesome, size: 15, color: K.aiInk),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text('${e['fieldLabel']}', style: K.body.copyWith(fontSize: 13, fontWeight: FontWeight.w500), overflow: TextOverflow.ellipsis),
                      Text('${e['participantId']}', style: K.mono.copyWith(fontSize: 11.5)),
                    ]),
                  ),
                  ConfMeter((e['confidence'] as num).toDouble()),
                ]),
              ),
            ),
      ]),
    );
  }

  Widget _alerts() {
    final alerts = d.dash['alerts'] as List;
    final ms = d.dash['milestones'] as List;
    final next = ms.cast<Map>().where((m) => m['done'] != true).firstOrNull;
    return Panel(
      title: 'Alerts and milestones',
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        if (alerts.isEmpty) const Text('No alerts', style: K.small),
        for (final a in alerts.take(2))
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Icon(a['severity'] == 'warning' ? Icons.warning_amber_rounded : Icons.info_outline, size: 16, color: a['severity'] == 'warning' ? K.aiInk : K.infoInk),
              const SizedBox(width: 8),
              Expanded(child: Text('${a['message']}', style: K.body.copyWith(fontSize: 13))),
            ]),
          ),
        if (next != null) ...[
          const Divider(),
          const SizedBox(height: 10),
          Row(children: [
            const Icon(Icons.flag_outlined, size: 16, color: K.ink2),
            const SizedBox(width: 8),
            Expanded(child: Text('Next: ${next['name']}', style: K.body.copyWith(fontSize: 13))),
            Text(fmtDate(next['date']), style: K.mono),
          ]),
        ],
      ]),
    );
  }

  Widget _tasks(BuildContext context) {
    final tasks = d.dash['tasks'] as List;
    return Panel(
      title: 'Tasks due',
      padding: EdgeInsets.zero,
      child: tasks.isEmpty
          ? const Padding(padding: EdgeInsets.all(K.s16), child: Text('No tasks due this week.', style: K.small))
          : Column(children: [
              for (final t in tasks.take(4))
                DataRow2(
                  flex: const [6, 3, 2],
                  onTap: t['participantId'] == null ? null : () => go(context, '/participants/${t['participantId']}'),
                  cells: [
                    Text('${t['title']}', style: K.body.copyWith(fontSize: 13), overflow: TextOverflow.ellipsis),
                    Text('${t['assignee']}', style: K.small, overflow: TextOverflow.ellipsis),
                    Text(fmtDate(t['due']), textAlign: TextAlign.right, style: K.mono),
                  ],
                ),
            ]),
    );
  }

  Widget _activity(BuildContext context) => Panel(
        title: 'Recent activity',
        trailing: LinkText('View audit trail', () => go(context, '/audit')),
        padding: EdgeInsets.zero,
        child: d.activity.isEmpty
            ? const Padding(padding: EdgeInsets.all(K.s16), child: Text('No activity recorded yet.', style: K.small))
            : Column(children: [
                for (final e in d.activity)
                  DataRow2(
                    height: 40,
                    flex: const [2, 4, 1],
                    cells: [
                      Text(fmtDateTime(e['ts']), style: K.mono.copyWith(fontSize: 11.5)),
                      Text('${e['actor']} · ${e['action']}', style: K.small.copyWith(color: K.ink), overflow: TextOverflow.ellipsis),
                      Align(alignment: Alignment.centerRight, child: Icon(e['source'] == 'ai' ? Icons.auto_awesome : Icons.person_outline, size: 14, color: e['source'] == 'ai' ? K.aiInk : K.ink2)),
                    ],
                  ),
              ]),
      );
}

/// Bars = new per month, line = cumulative, dashed line = target.
class RecruitmentPainter extends CustomPainter {
  final List<int> perMonth;
  final List<String> labels;
  final int target;
  RecruitmentPainter(this.perMonth, this.labels, this.target);

  @override
  void paint(Canvas canvas, Size s) {
    const left = 28.0, bottom = 20.0, top = 8.0;
    final w = s.width - left, h = s.height - bottom - top;
    final maxY = target.toDouble();
    double y(num v) => top + h - (v / maxY) * h;
    final grid = Paint()..color = K.line..strokeWidth = 1;
    void text(String t, Offset o, {Color c = K.ink3, TextAlign a = TextAlign.left}) {
      final tp = TextPainter(text: TextSpan(text: t, style: TextStyle(fontSize: 11, color: c, fontFeatures: const [FontFeature.tabularFigures()])), textDirection: TextDirection.ltr)..layout();
      tp.paint(canvas, a == TextAlign.right ? Offset(o.dx - tp.width, o.dy) : a == TextAlign.center ? Offset(o.dx - tp.width / 2, o.dy) : o);
    }

    for (var i = 0; i <= 4; i++) {
      final v = maxY * i / 4;
      canvas.drawLine(Offset(left, y(v)), Offset(s.width, y(v)), grid);
      text(v.round().toString(), Offset(left - 6, y(v) - 7), a: TextAlign.right);
    }
    final n = perMonth.length;
    final slot = w / n;
    final bar = Paint()..color = K.accent.withValues(alpha: .22);
    final pts = <Offset>[];
    var cum = 0;
    for (var i = 0; i < n; i++) {
      final cx = left + slot * (i + .5);
      final bw = (slot * .5).clamp(4.0, 22.0);
      if (perMonth[i] > 0) canvas.drawRRect(RRect.fromRectAndCorners(Rect.fromLTRB(cx - bw / 2, y(perMonth[i]), cx + bw / 2, y(0)), topLeft: const Radius.circular(2), topRight: const Radius.circular(2)), bar);
      cum += perMonth[i];
      pts.add(Offset(cx, y(cum)));
      if (n <= 8 || i.isEven) text(labels[i], Offset(cx, s.height - 14), a: TextAlign.center);
    }
    final line = Paint()..color = K.accent..strokeWidth = 2..style = PaintingStyle.stroke;
    canvas.drawPath(Path()..addPolygon(pts, false), line);
    for (final p in pts) {
      canvas.drawCircle(p, 3, Paint()..color = K.accent);
    }
    text('$cum', pts.last + const Offset(8, -16), c: K.accent);
    // dashed target line
    final dash = Paint()..color = K.chart3..strokeWidth = 1.5;
    for (double x = left; x < s.width; x += 8) {
      canvas.drawLine(Offset(x, y(target)), Offset((x + 4).clamp(0, s.width), y(target)), dash);
    }
  }

  @override
  bool shouldRepaint(RecruitmentPainter o) => o.perMonth != perMonth || o.target != target;
}
