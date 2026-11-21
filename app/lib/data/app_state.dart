import 'package:flutter/material.dart';
import '../models/models.dart';
import 'audit_store.dart';
import 'repository.dart';

/// Single app-wide state: repository-backed data + shared audit store.
/// Access anywhere: `AppScope.of(context)`.
class AppState extends ChangeNotifier {
  final DemoRepository repository;
  AppState({DemoRepository? repository}) : repository = repository ?? const JsonAssetRepository();

  late Dashboard dashboard;
  List<Participant> participants = [];
  final AuditStore audit = AuditStore();

  Participant? participant(String id) {
    for (final p in participants) {
      if (p.id == id) return p;
    }
    return null;
  }

  Future<void> load() async {
    dashboard = await repository.dashboard();
    participants = await repository.participants();
    notifyListeners();
  }
}

class AppScope extends InheritedWidget {
  final AppState state;
  const AppScope({super.key, required this.state, required super.child});
  static AppState of(BuildContext c) => c.getInheritedWidgetOfExactType<AppScope>()!.state;
  @override
  bool updateShouldNotify(AppScope o) => false; // listen via ListenableBuilder on state/audit
}
