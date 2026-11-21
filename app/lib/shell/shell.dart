import 'package:flutter/material.dart';
import 'package:zeta_flutter/zeta_flutter.dart';

const syntheticBanner = 'Synthetic data — prototype, not for clinical use';
const _tabs = [
  ('/', Icons.dashboard_outlined, 'Dashboard'),
  ('/participants', Icons.people_outline, 'Participants'),
  ('/review', Icons.fact_check_outlined, 'AI review'),
  ('/audit', Icons.history, 'Audit'),
];

/// Wraps every screen: synthetic-data banner + navigation rail.
class Shell extends StatelessWidget {
  final int selected;
  final Widget child;
  const Shell({super.key, required this.selected, required this.child});

  @override
  Widget build(BuildContext context) {
    final c = Zeta.of(context).colors;
    return Scaffold(
        body: Column(children: [
          Material(
            color: c.surfaceWarning,
            child: SizedBox(
              width: double.infinity,
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Text(syntheticBanner,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontWeight: FontWeight.w600, color: c.mainDefault)),
              ),
            ),
          ),
          Expanded(
            child: Row(children: [
              SizedBox(
                width: 112,
                child: ZetaNavigationRail(
                  selectedIndex: selected,
                  margin: const EdgeInsets.all(8),
                  onSelect: (i) {
                    if (i != selected) Navigator.of(context).pushReplacementNamed(_tabs[i].$1);
                  },
                  items: [
                    for (final t in _tabs) ZetaNavigationRailItem(icon: Icon(t.$2), label: t.$3),
                  ],
                ),
              ),
              const VerticalDivider(width: 1),
              Expanded(child: child),
            ]),
          ),
        ]),
      );
  }
}
