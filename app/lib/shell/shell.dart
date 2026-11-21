import 'package:flutter/material.dart';

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
  Widget build(BuildContext context) => Scaffold(
        body: Column(children: [
          Material(
            color: Colors.amber.shade200,
            child: SizedBox(
              width: double.infinity,
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Text(syntheticBanner,
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontWeight: FontWeight.w600, color: Colors.black87)),
              ),
            ),
          ),
          Expanded(
            child: Row(children: [
              NavigationRail(
                selectedIndex: selected,
                labelType: NavigationRailLabelType.all,
                onDestinationSelected: (i) {
                  if (i != selected) Navigator.of(context).pushReplacementNamed(_tabs[i].$1);
                },
                destinations: [
                  for (final t in _tabs)
                    NavigationRailDestination(icon: Icon(t.$2), label: Text(t.$3)),
                ],
              ),
              const VerticalDivider(width: 1),
              Expanded(child: child),
            ]),
          ),
        ]),
      );
}
