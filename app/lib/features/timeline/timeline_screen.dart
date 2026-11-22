import 'package:flutter/material.dart';
import '../../theme/tokens.dart';
import '../../ui/async.dart';
import '../../ui/format.dart';
import '../../ui/v4_widgets.dart';
import '../../ui/widgets.dart';

(IconData, String) catLook(String c) => switch (c) {
      'surgery' => (Icons.content_cut, 'Surgery'),
      'radiotherapy' => (Icons.radar, 'Radiotherapy'),
      'chemotherapy' => (Icons.medication_outlined, 'Chemotherapy'),
      'scan' => (Icons.image_search_outlined, 'Scan'),
      'visit' => (Icons.event_available_outlined, 'Visit'),
      'diagnosis' => (Icons.biotech_outlined, 'Diagnosis'),
      'lab' => (Icons.science_outlined, 'Lab'),
      _ => (Icons.circle_outlined, c),
    };

/// One line per participant: events in date order, each linked to its source document.
class TimelineScreen extends StatefulWidget {
  final String id;
  const TimelineScreen({super.key, required this.id});
  @override
  State<TimelineScreen> createState() => _TimelineScreenState();
}

class _TimelineScreenState extends State<TimelineScreen> {
  String cat = 'all';

  @override
  Widget build(BuildContext context) => Loader<Map>(
        load: (s) => s.run((a) async => await a.get('/participants/${widget.id}/timeline') as Map),
        builder: (c, tl, reload) {
          final all = [for (final e in tl['events'] as List) Map<String, dynamic>.from(e as Map)]..sort((x, y) => '${x['date']}'.compareTo('${y['date']}'));
          final cats = {for (final e in all) '${e['category']}'}.toList();
          final events = [for (final e in all) if (cat == 'all' || e['category'] == cat) e];
          return ListView(padding: const EdgeInsets.all(K.s24), children: [
            PageHeader(
              crumbs: [('Participants', '/participants'), (widget.id, '/participants/${widget.id}'), ('Timeline', null)],
              title: 'Timeline · ${widget.id}',
              subtitle: '${all.length} events from the source records. Each links to its document.',
            ),
            const SizedBox(height: K.s16),
            Wrap(spacing: 8, runSpacing: 6, children: [
              ChoiceChip(key: const Key('tl-all'), label: const Text('All'), selected: cat == 'all', onSelected: (_) => setState(() => cat = 'all')),
              for (final k in cats) ChoiceChip(key: Key('tl-$k'), avatar: Icon(catLook(k).$1, size: 16), label: Text(catLook(k).$2), selected: cat == k, onSelected: (_) => setState(() => cat = k)),
            ]),
            const SizedBox(height: K.s16),
            if (events.isEmpty)
              const Panel(child: EmptyState(icon: Icons.timeline, title: 'No events yet', hint: 'Sync the hospital record to build this timeline.'))
            else
              Panel(padding: EdgeInsets.zero, child: Column(children: [for (var i = 0; i < events.length; i++) _Event(events[i], last: i == events.length - 1)])),
          ]);
        },
      );
}

class _Event extends StatelessWidget {
  final Map e;
  final bool last;
  const _Event(this.e, {required this.last});
  @override
  Widget build(BuildContext context) {
    final (icon, label) = catLook('${e['category']}');
    final planned = e['status'] == 'planned' || e['status'] == 'scheduled';
    return Container(
      key: Key('ev-${e['id']}'),
      padding: const EdgeInsets.symmetric(horizontal: K.s16, vertical: 12),
      decoration: BoxDecoration(border: last ? null : const Border(bottom: BorderSide(color: K.line))),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SizedBox(width: 110, child: Text(fmtDate(e['date']) + (e['endDate'] != null ? '\n→ ${fmtDate(e['endDate'])}' : ''), style: K.mono)),
        Container(
          width: 30,
          height: 30,
          decoration: BoxDecoration(color: planned ? K.mutedBg : K.accentSoft, shape: BoxShape.circle, border: Border.all(color: planned ? K.mutedLine : K.infoLine)),
          child: Icon(icon, size: 16, color: planned ? K.mutedInk : K.accent),
        ),
        const SizedBox(width: K.s12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Flexible(child: Text('${e['title']}', style: K.heading)),
              const SizedBox(width: 8),
              Pill(planned ? 'Planned' : label, tone: Tone.muted),
            ]),
            if (e['detail'] != null) Padding(padding: const EdgeInsets.only(top: 2), child: Text('${e['detail']}', style: K.small.copyWith(fontSize: 13))),
            if (e['documentId'] != null)
              TextButton.icon(
                key: Key('doc-${e['id']}'),
                style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(0, 28), foregroundColor: K.infoInk),
                onPressed: () => showDocument(context, '${e['documentId']}'),
                icon: const Icon(Icons.link, size: 16),
                label: Text('${e['documentId']}${e['documentTitle'] != null ? ' · ${e['documentTitle']}' : ''}'),
              ),
          ]),
        ),
      ]),
    );
  }
}
