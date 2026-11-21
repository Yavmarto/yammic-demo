import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/models.dart';
import 'audit_store.dart';

/// Single app-wide state: bundled JSON + shared audit store.
/// Access anywhere: `AppScope.of(context)`.
class AppState extends ChangeNotifier {
  late Dashboard dashboard;
  List<Participant> participants = [];
  List<AiExtraction> extractions = [];
  final AuditStore audit = AuditStore();

  Participant? participant(String id) {
    for (final p in participants) {
      if (p.id == id) return p;
    }
    return null;
  }

  Future<Map<String, dynamic>> _load(String f) async =>
      jsonDecode(await rootBundle.loadString('assets/data/$f')) as Map<String, dynamic>;

  Future<void> load() async {
    dashboard = Dashboard.fromJson(await _load('dashboard.json'));
    final p = await _load('participants.json');
    participants = (p['participants'] as List).map((e) => Participant.fromJson(e)).toList();
    try {
      final x = await _load('extractions.json'); // optional until data task lands
      extractions = (x['extractions'] as List).map((e) => AiExtraction.fromJson(e)).toList();
    } catch (_) {}
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
