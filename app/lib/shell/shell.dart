import 'package:flutter/material.dart';
import '../data/app_state.dart';
import '../features/review/review_store.dart';
import '../theme/tokens.dart';
import '../ui/widgets.dart';

const syntheticBanner = 'Synthetic data — prototype, not for clinical use';
const _tabs = [
  ('/', Icons.space_dashboard_outlined, Icons.space_dashboard, 'Dashboard'),
  ('/participants', Icons.people_outline, Icons.people, 'Participants'),
  ('/review', Icons.fact_check_outlined, Icons.fact_check, 'AI review'),
  ('/audit', Icons.history, Icons.history, 'Audit trail'),
];

/// Wraps every screen: synthetic-data banner + sidebar navigation.
class Shell extends StatelessWidget {
  final int selected;
  final Widget child;
  const Shell({super.key, required this.selected, required this.child});

  @override
  Widget build(BuildContext context) {
    final app = AppScope.of(context);
    final store = ReviewStore.of(app.audit, app.repository)..load();
    return Scaffold(
      backgroundColor: K.bg,
      body: Column(children: [
        const _Banner(),
        Expanded(
          child: LayoutBuilder(builder: (context, box) {
            final wide = box.maxWidth >= 1000;
            return Row(children: [
              ListenableBuilder(
                listenable: store,
                builder: (_, _) => _Sidebar(
                  selected: selected,
                  wide: wide,
                  pending: store.loaded ? store.pending(null) : null,
                ),
              ),
              Expanded(child: FadeIn(key: ValueKey(selected), child: child)),
            ]);
          }),
        ),
      ]),
    );
  }
}

class _Banner extends StatelessWidget {
  const _Banner();
  @override
  Widget build(BuildContext context) => Semantics(
        container: true,
        label: syntheticBanner,
        child: Container(
          width: double.infinity,
          height: 30,
          decoration: const BoxDecoration(color: K.aiBg, border: Border(bottom: BorderSide(color: K.aiLine, width: 1))),
          alignment: Alignment.center,
          child: const Row(mainAxisSize: MainAxisSize.min, children: [
            Icon(Icons.science_outlined, size: 14, color: K.aiInk),
            SizedBox(width: 8),
            Text(syntheticBanner, style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600, color: K.aiInk)),
          ]),
        ),
      );
}

class _Sidebar extends StatelessWidget {
  final int selected;
  final bool wide;
  final int? pending;
  const _Sidebar({required this.selected, required this.wide, required this.pending});

  @override
  Widget build(BuildContext context) => Container(
        width: wide ? 232 : 76,
        decoration: const BoxDecoration(color: K.sidebar, border: Border(right: BorderSide(color: K.line))),
        padding: EdgeInsets.symmetric(horizontal: wide ? 12 : 10, vertical: 16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Padding(
            padding: EdgeInsets.fromLTRB(wide ? 8 : 0, 4, 8, 20),
            child: Row(mainAxisAlignment: wide ? MainAxisAlignment.start : MainAxisAlignment.center, children: [
              Container(
                width: 30,
                height: 30,
                alignment: Alignment.center,
                decoration: BoxDecoration(color: K.ink, borderRadius: BorderRadius.circular(8)),
                child: const Text('Y', style: TextStyle(color: K.surface, fontWeight: FontWeight.w700, fontSize: 16)),
              ),
              if (wide) ...[
                const SizedBox(width: 10),
                const Text('Yammic', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600, letterSpacing: -0.2, color: K.ink)),
              ],
            ]),
          ),
          for (var i = 0; i < _tabs.length; i++)
            _NavItem(
              icon: i == selected ? _tabs[i].$3 : _tabs[i].$2,
              label: _tabs[i].$4,
              selected: i == selected,
              wide: wide,
              badge: i == 2 && (pending ?? 0) > 0 ? '$pending' : null,
              onTap: () {
                if (i != selected) Navigator.of(context).pushReplacementNamed(_tabs[i].$1);
              },
            ),
          const Spacer(),
          if (wide)
            const Padding(
              padding: EdgeInsets.fromLTRB(8, 0, 8, 8),
              child: Row(children: [
                CircleAvatar(radius: 14, backgroundColor: K.accentSoft, child: Text('JD', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: K.accent))),
                SizedBox(width: 10),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(reviewerId, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: K.ink)),
                    Text('Data reviewer', style: TextStyle(fontSize: 12, color: K.ink3)),
                  ]),
                ),
              ]),
            ),
        ]),
      );
}

class _NavItem extends StatefulWidget {
  final IconData icon;
  final String label;
  final bool selected, wide;
  final String? badge;
  final VoidCallback onTap;
  const _NavItem({required this.icon, required this.label, required this.selected, required this.wide, required this.onTap, this.badge});
  @override
  State<_NavItem> createState() => _NavItemState();
}

class _NavItemState extends State<_NavItem> {
  bool hover = false;
  @override
  Widget build(BuildContext context) {
    final sel = widget.selected;
    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Semantics(
        button: true,
        selected: sel,
        label: widget.label,
        child: MouseRegion(
          onEnter: (_) => setState(() => hover = true),
          onExit: (_) => setState(() => hover = false),
          cursor: SystemMouseCursors.click,
          child: GestureDetector(
            onTap: widget.onTap,
            behavior: HitTestBehavior.opaque,
            child: AnimatedContainer(
              duration: K.fast,
              curve: K.ease,
              height: 40,
              padding: EdgeInsets.symmetric(horizontal: widget.wide ? 10 : 0),
              decoration: BoxDecoration(
                color: sel ? K.surface : hover ? K.line.withValues(alpha: .6) : Colors.transparent,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: sel ? K.line : Colors.transparent),
              ),
              child: Row(mainAxisAlignment: widget.wide ? MainAxisAlignment.start : MainAxisAlignment.center, children: [
                Icon(widget.icon, size: 20, color: sel ? K.accent : K.ink2),
                if (widget.wide) ...[
                  const SizedBox(width: 12),
                  Expanded(child: Text(widget.label, style: TextStyle(fontSize: 14, fontWeight: sel ? FontWeight.w600 : FontWeight.w500, color: sel ? K.ink : K.ink2))),
                  if (widget.badge != null)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 1),
                      decoration: BoxDecoration(color: K.aiBg, border: Border.all(color: K.aiLine), borderRadius: BorderRadius.circular(999)),
                      child: Text(widget.badge!, style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700, color: K.aiInk)),
                    ),
                ],
              ]),
            ),
          ),
        ),
      ),
    );
  }
}
