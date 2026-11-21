import 'package:flutter/foundation.dart';
import '../models/models.dart';

/// In-memory, append-only audit log. No remove/edit API by design.
class AuditStore extends ChangeNotifier {
  final List<AuditEvent> _events = [];
  List<AuditEvent> get events => List.unmodifiable(_events);

  void record({
    required String actor,
    required String action,
    required String field,
    String? before,
    String? after,
    required EventSource source,
    String? model,
    String? promptVersion,
  }) {
    _events.add(AuditEvent(
      actor: actor, action: action, field: field, before: before, after: after,
      source: source, model: model, promptVersion: promptVersion,
      timestamp: DateTime.now(),
    ));
    notifyListeners();
  }
}
