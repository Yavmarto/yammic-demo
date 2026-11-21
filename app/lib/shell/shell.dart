import 'package:flutter/material.dart';
import '../data/session.dart';
import '../theme/tokens.dart';
import '../ui/widgets.dart';

const syntheticBanner = 'Synthetic data — prototype, not for clinical use';

class _Tab {
  final String route, label;
  final IconData icon;
  const _Tab(this.route, this.label, this.icon);
}

const _study = [
  _Tab('/', 'Dashboard', Icons.space_dashboard_outlined),
  _Tab('/participants', 'Participants', Icons.people_outline),
  _Tab('/review', 'AI review', Icons.fact_check_outlined),
  _Tab('/queries', 'Queries', Icons.help_outline),
  _Tab('/audit', 'Audit trail', Icons.history),
];
const _platform = [
  _Tab('/integrations', 'Integrations', Icons.hub_outlined),
  _Tab('/ai-quality', 'AI quality', Icons.insights_outlined),
  _Tab('/export', 'Export', Icons.ios_share_outlined),
];

String roleLabel(String r) => switch (r) { 'nurse' => 'Research nurse', 'monitor' => 'Monitor', 'pi' => 'Principal investigator', _ => r };

/// Synthetic banner + sidebar + top context bar + offline banner around every signed-in screen.
class Shell extends StatelessWidget {
  final String selected;
  final Widget child;
  const Shell({super.key, required this.selected, required this.child});

  @override
  Widget build(BuildContext context) {
    final s = SessionScope.of(context);
    return Scaffold(
      backgroundColor: K.bg,
      body: Column(children: [
        const SyntheticBanner(),
        Expanded(
          child: LayoutBuilder(builder: (context, box) {
            final wide = box.maxWidth >= 1280 && selected != '/review';
            return Row(children: [
              _Sidebar(selected: selected, wide: wide, s: s),
              Expanded(
                child: Column(children: [
                  _TopBar(s: s, selected: selected),
                  if (s.offline) _OfflineBanner(s: s),
                  if (s.isMonitor && !s.offline) const _ReadOnlyBanner(),
                  Expanded(child: child),
                ]),
              ),
            ]);
          }),
        ),
      ]),
    );
  }
}

/// Always visible, never dismissible.
class SyntheticBanner extends StatelessWidget {
  const SyntheticBanner({super.key});
  @override
  Widget build(BuildContext context) => Semantics(
        container: true,
        label: syntheticBanner,
        child: Container(
          width: double.infinity,
          constraints: const BoxConstraints(minHeight: 28),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          decoration: const BoxDecoration(color: K.aiBg, border: Border(bottom: BorderSide(color: Color(0xFFF0D3A8)))),
          child: const Row(children: [
            Icon(Icons.science_outlined, size: 14, color: K.aiInk),
            SizedBox(width: 8),
            Expanded(child: Text(syntheticBanner, style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w500, color: K.aiInk))),
            Pill('DEMO', tone: Tone.ai),
          ]),
        ),
      );
}

class _OfflineBanner extends StatelessWidget {
  final Session s;
  const _OfflineBanner({required this.s});
  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: K.s24, vertical: 6),
        decoration: const BoxDecoration(color: K.sidebar, border: Border(bottom: BorderSide(color: K.line))),
        child: Row(children: [
          const Icon(Icons.cloud_off, size: 16, color: K.mutedInk),
          const SizedBox(width: 8),
          const Expanded(child: Text('Offline snapshot. Read-only until the local backend reconnects.', style: TextStyle(fontSize: 13, color: K.mutedInk, fontWeight: FontWeight.w500))),
          TextButton(onPressed: s.retryOnline, child: const Text('Retry')),
        ]),
      );
}

class _ReadOnlyBanner extends StatelessWidget {
  const _ReadOnlyBanner();
  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: K.s24, vertical: 6),
        decoration: const BoxDecoration(color: K.infoBg, border: Border(bottom: BorderSide(color: K.line))),
        child: const Row(children: [
          Icon(Icons.visibility_outlined, size: 16, color: K.infoInk),
          SizedBox(width: 8),
          Text('Monitor role is read-only in this demo.', style: TextStyle(fontSize: 13, color: K.infoInk, fontWeight: FontWeight.w500)),
        ]),
      );
}

/// Teal = connected, grey = offline snapshot (never green: green means human-verified).
class ConnectionPill extends StatelessWidget {
  final Session s;
  const ConnectionPill(this.s, {super.key});
  @override
  Widget build(BuildContext context) {
    final off = s.offline;
    final fg = off ? K.mutedInk : K.tealInk;
    return Semantics(
      label: off ? 'Offline snapshot' : 'Connected to local backend',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: off ? K.mutedBg : K.tealBg,
          border: Border.all(color: off ? K.mutedLine : K.teal),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(off ? Icons.cloud_off : Icons.link, size: 14, color: fg),
          const SizedBox(width: 6),
          Text(off ? 'Offline snapshot' : 'Connected${s.latencyMs != null ? ' · ${s.latencyMs} ms' : ''}', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: fg)),
        ]),
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  final Session s;
  final String selected;
  const _TopBar({required this.s, required this.selected});
  @override
  Widget build(BuildContext context) {
    final all = [..._study, ..._platform];
    final here = all.where((t) => t.route == selected).firstOrNull?.label ?? 'Participants';
    return Container(
      height: 56,
      padding: const EdgeInsets.symmetric(horizontal: K.s24),
      decoration: const BoxDecoration(color: K.surface, border: Border(bottom: BorderSide(color: K.line))),
      child: Row(children: [
        Flexible(child: Text('GBM-NL-2026-01', overflow: TextOverflow.ellipsis, style: K.small.copyWith(color: K.ink3))),
        const Padding(padding: EdgeInsets.symmetric(horizontal: 6), child: Icon(Icons.chevron_right, size: 14, color: K.ink3)),
        Flexible(child: Text(here, overflow: TextOverflow.ellipsis, style: K.small.copyWith(color: K.ink, fontWeight: FontWeight.w500))),
        const Spacer(),
        if (MediaQuery.sizeOf(context).width >= 1100) ...[Text('Data as of 23 Nov 2026', style: K.small), const SizedBox(width: K.s16)],
        ConnectionPill(s),
        const SizedBox(width: K.s16),
        _UserMenu(s: s),
      ]),
    );
  }
}

class _UserMenu extends StatelessWidget {
  final Session s;
  const _UserMenu({required this.s});
  @override
  Widget build(BuildContext context) => PopupMenuButton<String>(
        tooltip: 'Account',
        offset: const Offset(0, 40),
        onSelected: (_) => s.logout(),
        itemBuilder: (_) => [
          PopupMenuItem(enabled: false, child: Text('${s.userName}\n${roleLabel(s.role)}', style: K.small)),
          const PopupMenuItem(value: 'switch', child: Text('Switch demo role')),
        ],
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          CircleAvatar(radius: 16, backgroundColor: K.accentSoft, child: Text(s.username.isEmpty ? '?' : s.username.substring(0, s.username.length > 1 ? 2 : 1).toUpperCase(), style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: K.accent))),
          const SizedBox(width: 8),
          Text(roleLabel(s.role), style: K.small.copyWith(color: K.ink)),
          const Icon(Icons.arrow_drop_down, color: K.ink3),
        ]),
      );
}

class _Sidebar extends StatelessWidget {
  final String selected;
  final bool wide;
  final Session s;
  const _Sidebar({required this.selected, required this.wide, required this.s});

  Widget _section(BuildContext c, String title, List<_Tab> tabs) => Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        if (wide) Padding(padding: const EdgeInsets.fromLTRB(10, 14, 0, 6), child: Text(title, style: K.label)) else const SizedBox(height: 14),
        for (final t in tabs)
          _NavItem(
            icon: t.icon,
            label: t.label,
            selected: t.route == selected,
            wide: wide,
            badge: t.route == '/review' && (s.pending ?? 0) > 0 ? '${s.pending}' : null,
            onTap: () {
              if (t.route != selected) Navigator.of(c).pushReplacementNamed(t.route);
            },
          ),
      ]);

  @override
  Widget build(BuildContext context) => AnimatedContainer(
        duration: K.fast,
        width: wide ? 232 : 72,
        decoration: const BoxDecoration(color: K.sidebar, border: Border(right: BorderSide(color: K.line))),
        padding: EdgeInsets.symmetric(horizontal: wide ? 12 : 10, vertical: 16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Padding(
            padding: EdgeInsets.fromLTRB(wide ? 8 : 0, 4, 8, 6),
            child: Row(mainAxisAlignment: wide ? MainAxisAlignment.start : MainAxisAlignment.center, children: [
              Container(
                width: 28,
                height: 28,
                alignment: Alignment.center,
                decoration: BoxDecoration(color: K.ink, borderRadius: BorderRadius.circular(7)),
                child: const Text('Y', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w500, fontSize: 15)),
              ),
              if (wide) ...[
                const SizedBox(width: 10),
                const Text('Yammic', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w500, letterSpacing: -.2, color: K.ink)),
              ],
            ]),
          ),
          _section(context, 'STUDY', _study),
          _section(context, 'PLATFORM', _platform),
          const Spacer(),
          if (wide)
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 0, 8, 4),
              child: Text('FHIR R4 · Postgres 16\nlocal demo stack', style: K.small.copyWith(color: K.ink3, fontSize: 11.5)),
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
        child: Tooltip(
          message: widget.wide ? '' : widget.label,
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
                  color: sel ? K.accentSoft : hover ? K.line.withValues(alpha: .6) : Colors.transparent,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(mainAxisAlignment: widget.wide ? MainAxisAlignment.start : MainAxisAlignment.center, children: [
                  Stack(clipBehavior: Clip.none, children: [
                    Icon(widget.icon, size: 20, color: sel ? K.accent : K.ink2),
                    if (!widget.wide && widget.badge != null)
                      const Positioned(right: -3, top: -2, child: CircleAvatar(radius: 4, backgroundColor: K.aiLine)),
                  ]),
                  if (widget.wide) ...[
                    const SizedBox(width: 12),
                    Expanded(child: Text(widget.label, style: TextStyle(fontSize: 14, fontWeight: sel ? FontWeight.w500 : FontWeight.w400, color: sel ? K.ink : K.ink2))),
                    if (widget.badge != null)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 1),
                        decoration: BoxDecoration(color: K.aiBg, border: Border.all(color: K.aiLine), borderRadius: BorderRadius.circular(999)),
                        child: Text(widget.badge!, style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w500, color: K.aiInk)),
                      ),
                  ],
                ]),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
