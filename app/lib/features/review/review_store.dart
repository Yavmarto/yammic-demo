import 'package:flutter/foundation.dart';
import '../../data/audit_store.dart';
import '../../data/repository.dart';
import '../../models/models.dart';

enum RState { unverified, accepted, corrected, rejected, deferred }

const reviewerId = 'SYN-JD';

/// One pre-computed AI extraction (richer than models.AiExtraction; read straight from the asset).
class ReviewItem {
  final Map<String, dynamic> j;
  ReviewItem(this.j);
  String get id => j['id'];
  String get participantId => j['participantId'];
  String get field => j['field'];
  String get label => j['fieldLabel'] ?? field;
  String get value => j['value'];
  String get unit => j['unit'] ?? '';
  String get docId => j['documentId'] ?? '';
  String get docType => (j['documentType'] ?? '').toString().replaceAll('_', ' ');
  String get text => j['sourceText'];
  double get confidence => (j['confidence'] as num).toDouble();
  bool get abstained => j['status'] == 'abstained';
  String get model => j['model'] ?? '';
  String get prompt => j['promptVersion'] ?? '';
  Map<String, dynamic>? get code => j['proposedCode'];
  int get start => (j['spanStart'] as num?)?.toInt() ?? -1;
  int get end => (j['spanEnd'] as num?)?.toInt() ?? -1;
  bool get spanValid => !abstained && start >= 0 && end > start && end <= text.length;
  bool get canAccept => spanValid && !abstained;
  /// Audit rows have no participant column; the field string carries it.
  String get auditField => '$participantId · $label';
}

class ReviewStore extends ChangeNotifier {
  final AuditStore audit;
  final DemoRepository repo;
  ReviewStore(this.audit, [DemoRepository? repo]) : repo = repo ?? const JsonAssetRepository();
  static ReviewStore? _shared;
  static ReviewStore of(AuditStore a, [DemoRepository? r]) =>
      (_shared?.audit == a) ? _shared! : (_shared = ReviewStore(a, r));

  List<ReviewItem> items = [];
  final Map<String, RState> state = {};
  final Map<String, String> corrected = {}, reason = {};
  Object? error;
  bool loaded = false;

  RState stateOf(ReviewItem i) => state[i.id] ?? RState.unverified;
  int pending(String? pid) => items
      .where((i) => (pid == null || i.participantId == pid) && stateOf(i) == RState.unverified)
      .length;

  Future<void> load() async {
    if (loaded) return;
    error = null;
    try {
      items = [for (final e in await repo.extractions()) ReviewItem(e)];
      // AI "extract" events once, so the audit trail shows AI vs human provenance.
      if (!audit.events.any((e) => e.action == 'extract')) {
        for (final i in items) {
          audit.record(actor: i.model, action: 'extract', field: i.auditField, after: i.value,
              source: EventSource.ai, model: i.model, promptVersion: i.prompt);
        }
      }
      loaded = true;
    } catch (e) {
      error = e;
    }
    notifyListeners();
  }

  void act(ReviewItem i, String action, {String? value, String? why}) {
    final s = {'accept': RState.accepted, 'correct': RState.corrected, 'reject': RState.rejected, 'defer': RState.deferred}[action]!;
    state[i.id] = s;
    if (action == 'correct') corrected[i.id] = value!;
    if (action == 'reject') reason[i.id] = why ?? '';
    audit.record(
      actor: reviewerId, action: action, field: i.auditField,
      before: action == 'accept' ? null : i.value,
      after: switch (action) { 'accept' => i.value, 'correct' => value, 'reject' => 'rejected: $why', _ => null },
      source: EventSource.human, model: i.model, promptVersion: i.prompt,
    );
    notifyListeners();
  }

  /// Demo rule set: required, KPS 0-100 numeric.
  String? validate(ReviewItem i, String v) {
    if (v.trim().isEmpty) return 'Value is required';
    if (i.field == 'KPS') {
      final n = int.tryParse(v.trim());
      if (n == null || n < 0 || n > 100) return 'KPS must be 0–100';
    }
    return null;
  }
}
