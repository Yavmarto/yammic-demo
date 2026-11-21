import 'package:flutter/material.dart';
import '../theme/tokens.dart';

/// Flat bordered surface. Hairline, no shadow, no nesting.
class Panel extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final String? title;
  final Widget? trailing;
  const Panel({super.key, required this.child, this.padding = const EdgeInsets.all(K.s16), this.title, this.trailing});

  @override
  Widget build(BuildContext context) => DecoratedBox(
        decoration: BoxDecoration(
          color: K.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: K.line),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, mainAxisSize: MainAxisSize.min, children: [
          if (title != null) ...[
            Padding(
              padding: const EdgeInsets.fromLTRB(K.s16, 14, K.s16, 12),
              child: Row(children: [
                Expanded(child: Text(title!.toUpperCase(), style: K.label)),
                ?trailing,
              ]),
            ),
            const Divider(),
          ],
          Padding(padding: padding, child: child),
        ]),
      );
}

/// Page title block with optional breadcrumb and trailing actions.
class PageHeader extends StatelessWidget {
  final String title;
  final String? subtitle;
  final List<(String, String?)> crumbs; // (label, route|null)
  final Widget? trailing;
  const PageHeader({super.key, required this.title, this.subtitle, this.crumbs = const [], this.trailing});

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        if (crumbs.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Row(children: [
              for (var i = 0; i < crumbs.length; i++) ...[
                if (i > 0) const Padding(padding: EdgeInsets.symmetric(horizontal: 6), child: Icon(Icons.chevron_right, size: 14, color: K.ink3)),
                InkWell(
                  onTap: crumbs[i].$2 == null ? null : () => Navigator.of(context).pushReplacementNamed(crumbs[i].$2!),
                  child: Text(crumbs[i].$1, style: K.small.copyWith(color: crumbs[i].$2 == null ? K.ink3 : K.accent)),
                ),
              ],
            ]),
          ),
        Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(title, style: K.display),
              if (subtitle != null) Padding(padding: const EdgeInsets.only(top: 4), child: Text(subtitle!, style: K.small.copyWith(fontSize: 14))),
            ]),
          ),
          ?trailing,
        ]),
      ]);
}

enum Tone { ai, ok, bad, info, muted }

(Color, Color, Color) toneColors(Tone t) => switch (t) {
      Tone.ai => (K.aiBg, K.aiLine, K.aiInk),
      Tone.ok => (K.okBg, K.okLine, K.okInk),
      Tone.bad => (K.badBg, K.badLine, K.badInk),
      Tone.info => (K.infoBg, K.infoLine, K.infoInk),
      Tone.muted => (K.mutedBg, K.mutedLine, K.mutedInk),
    };

/// Icon + text status pill. Colour is never the only signal.
class Pill extends StatelessWidget {
  final String label;
  final Tone tone;
  final IconData? icon;
  const Pill(this.label, {super.key, this.tone = Tone.muted, this.icon});
  @override
  Widget build(BuildContext context) {
    final (bg, line, ink) = toneColors(tone);
    return Semantics(
      label: 'Status: $label',
      excludeSemantics: true,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(color: bg, border: Border.all(color: line.withValues(alpha: .6)), borderRadius: BorderRadius.circular(999)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          if (icon != null) ...[Icon(icon, size: 13, color: ink), const SizedBox(width: 4)],
          Flexible(child: Text(label, overflow: TextOverflow.ellipsis, style: TextStyle(color: ink, fontWeight: FontWeight.w600, fontSize: 12, height: 1.3))),
        ]),
      ),
    );
  }
}

/// Animated horizontal bar. `value` 0..1.
class Bar extends StatelessWidget {
  final double value;
  final Color color;
  final double height;
  const Bar(this.value, {super.key, this.color = K.accent, this.height = 6});
  @override
  Widget build(BuildContext context) => ClipRRect(
        borderRadius: BorderRadius.circular(height),
        child: Container(
          height: height,
          color: K.line,
          alignment: Alignment.centerLeft,
          child: TweenAnimationBuilder<double>(
            tween: Tween(end: value.clamp(0, 1)),
            duration: const Duration(milliseconds: 420),
            curve: K.ease,
            builder: (_, v, _) => FractionallySizedBox(widthFactor: v, child: Container(color: color)),
          ),
        ),
      );
}

/// Keyboard hint chip.
class Kbd extends StatelessWidget {
  final String k;
  final Color? color;
  const Kbd(this.k, {super.key, this.color});
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
        decoration: BoxDecoration(border: Border.all(color: color ?? K.lineStrong), borderRadius: BorderRadius.circular(4)),
        child: Text(k, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color ?? K.ink3, height: 1.4)),
      );
}

/// Fades content in once (state change, not decoration): 180ms.
class FadeIn extends StatelessWidget {
  final Widget child;
  const FadeIn({super.key, required this.child});
  @override
  Widget build(BuildContext context) => TweenAnimationBuilder<double>(
        tween: Tween(begin: 0, end: 1),
        duration: const Duration(milliseconds: 180),
        curve: K.ease,
        builder: (_, v, c) => Opacity(opacity: v, child: c),
        child: child,
      );
}

/// Empty state that tells the user what to do next.
class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title, hint;
  final Widget? action;
  const EmptyState({super.key, required this.icon, required this.title, required this.hint, this.action});
  @override
  Widget build(BuildContext context) => Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 380),
          child: Padding(
            padding: const EdgeInsets.all(K.s24),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(color: K.accentSoft, borderRadius: BorderRadius.circular(12)),
                child: Icon(icon, color: K.accent, size: 24),
              ),
              const SizedBox(height: K.s16),
              Text(title, style: K.heading, textAlign: TextAlign.center),
              const SizedBox(height: 6),
              Text(hint, style: K.small.copyWith(fontSize: 13.5), textAlign: TextAlign.center),
              if (action != null) ...[const SizedBox(height: K.s16), action!],
            ]),
          ),
        ),
      );
}

/// Error state with retry.
class ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;
  const ErrorState({super.key, required this.message, this.onRetry});
  @override
  Widget build(BuildContext context) => Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.error_outline, color: K.badLine, size: 32),
            const SizedBox(height: K.s12),
            const Text('Could not load data', style: K.heading),
            const SizedBox(height: 6),
            Text(message, style: K.small, textAlign: TextAlign.center),
            if (onRetry != null) ...[const SizedBox(height: K.s16), OutlinedButton(onPressed: onRetry, child: const Text('Try again'))],
          ]),
        ),
      );
}

/// Pulsing placeholder block for loading states.
class Skeleton extends StatefulWidget {
  final double? width;
  final double height;
  const Skeleton({super.key, this.width, this.height = 16});
  @override
  State<Skeleton> createState() => _SkeletonState();
}

class _SkeletonState extends State<Skeleton> with SingleTickerProviderStateMixin {
  late final c = AnimationController(vsync: this, duration: const Duration(milliseconds: 1100))..repeat(reverse: true);
  @override
  void dispose() {
    c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
        animation: c,
        builder: (_, _) => Container(
          width: widget.width,
          height: widget.height,
          decoration: BoxDecoration(color: Color.lerp(K.line, K.sidebar, c.value), borderRadius: BorderRadius.circular(6)),
        ),
      );
}

/// Whole-page skeleton shown while data loads.
class PageSkeleton extends StatelessWidget {
  const PageSkeleton({super.key});
  @override
  Widget build(BuildContext context) => const Padding(
        padding: EdgeInsets.all(K.s32),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Skeleton(width: 240, height: 28),
          SizedBox(height: K.s8),
          Skeleton(width: 360),
          SizedBox(height: K.s32),
          Row(children: [
            Expanded(child: Skeleton(height: 180)),
            SizedBox(width: K.s16),
            Expanded(child: Skeleton(height: 180)),
          ]),
          SizedBox(height: K.s16),
          Skeleton(height: 220),
        ]),
      );
}

Tone statusTone(String s) => switch (s) {
      'active' || 'enrolled' || 'complete' || 'completed' => Tone.ok,
      'screening' || 'in_progress' || 'scheduled' => Tone.info,
      'awaiting_review' => Tone.ai,
      'withdrawn' || 'missed' => Tone.bad,
      _ => Tone.muted,
    };
