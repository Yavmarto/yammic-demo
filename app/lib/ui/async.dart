import 'package:flutter/material.dart';
import '../data/session.dart';
import 'widgets.dart';

/// Loads data via the session (offline fallback built in) with skeleton / error / retry.
class Loader<T> extends StatefulWidget {
  final Future<T> Function(Session s) load;
  final Widget Function(BuildContext, T, VoidCallback reload) builder;
  final Widget? skeleton;
  const Loader({super.key, required this.load, required this.builder, this.skeleton});
  @override
  State<Loader<T>> createState() => _LoaderState<T>();
}

class _LoaderState<T> extends State<Loader<T>> {
  late Future<T> f;
  Session? s;
  bool _init = false;

  void _reload() => setState(() => f = widget.load(s!));

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    s = SessionScope.read(context);
    if (!_init) {
      _init = true;
      f = widget.load(s!);
    }
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<T>(
        future: f,
        builder: (c, snap) {
          if (snap.hasError) return ErrorState(message: '${snap.error}', onRetry: _reload);
          if (!snap.hasData) return widget.skeleton ?? const PageSkeleton();
          return widget.builder(c, snap.data as T, _reload);
        },
      );
}
