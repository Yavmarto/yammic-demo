import 'package:flutter/foundation.dart';
import '../../api/api.dart';
import '../../data/session.dart';

enum RState { unverified, accepted, corrected, rejected, deferred }

/// One AI proposal from GET /participants/{id}/extractions.
class ReviewItem {
  Map<String, dynamic> j;
  String text = '';
  ReviewItem(this.j);
  String get id => j['id'];
  String? get assignedTo => j['assignedTo'];
  String? get dueDate => j['dueDate'];
  String get participantId => j['participantId'];
  String get field => j['field'];
  String get label => j['fieldLabel'] ?? field;
  String get value => j['value'] ?? '';
  String get unit => j['unit'] ?? '';
  String get docId => j['documentId'] ?? '';
  String get docType => (j['documentType'] ?? '').toString().replaceAll('_', ' ');
  double get confidence => (j['confidence'] as num).toDouble();
  bool get abstained => j['status'] == 'abstained';
  String get model => j['model'] ?? '';
  String get prompt => j['promptVersion'] ?? '';
  String get provider => j['provider'] ?? '';
  Map<String, dynamic>? get code => j['proposedCode'];
  int get start => (j['spanStart'] as num?)?.toInt() ?? -1;
  int get end => (j['spanEnd'] as num?)?.toInt() ?? -1;
  bool get spanValid => !abstained && start >= 0 && end > start && end <= text.length;
  bool get canAccept => spanValid;
  Map? get last => j['lastDecision'];
  String? get correctedValue => last?['correctedValue'];
  String? get reason => last?['reason'];
  RState get state => switch (j['reviewState']) {
        'accepted' => RState.accepted,
        'corrected' => RState.corrected,
        'rejected' => RState.rejected,
        'deferred' => RState.deferred,
        _ => RState.unverified,
      };
}

class ReviewStore extends ChangeNotifier {
  final Session session;
  ReviewStore(this.session);

  List<ReviewItem> items = [];
  List<String> participantIds = [];
  final _docs = <String, String>{};
  Object? error;
  bool loaded = false;

  int pending(String? pid) => items.where((i) => (pid == null || i.participantId == pid) && i.state == RState.unverified).length;

  Future<void> load() async {
    error = null;
    try {
      final all = await session.run((a) async {
        final ps = (await a.get('/participants') as List).where((p) => (p['documentCount'] as int) > 0).toList();
        final out = <ReviewItem>[];
        final ids = <String>[];
        for (final p in ps) {
          ids.add(p['id']);
          for (final e in await a.get('/participants/${p['id']}/extractions') as List) {
            out.add(ReviewItem(Map<String, dynamic>.from(e)));
          }
        }
        for (final d in {for (final i in out) i.docId}) {
          _docs[d] ??= (await a.get('/documents/$d') as Map)['text'] as String;
        }
        participantIds = ids;
        return out;
      });
      for (final i in all) {
        i.text = _docs[i.docId] ?? '';
      }
      items = all;
      session.setPending(pending(null));
      loaded = true;
    } catch (e) {
      error = e;
    }
    notifyListeners();
  }

  /// POSTs the decision; the backend writes the eCRF value and the audit event.
  Future<String?> act(ReviewItem i, String action, {String? value, String? why}) async {
    try {
      final r = await session.api.post('/extractions/${i.id}/decision', {
        'decision': action,
        'correctedValue': ?value,
        'reason': ?why,
      }) as Map;
      i.j = {...Map<String, dynamic>.from(r['extraction']), };
      session.setPending(pending(null));
      notifyListeners();
      return null;
    } on ApiException catch (e) {
      return e.message;
    } on Unreachable catch (e) {
      session.markOffline();
      return e.message;
    }
  }

  /// Demo rule set: required, KPS 0-100 numeric (server validates the rest).
  String? validate(ReviewItem i, String v) {
    if (v.trim().isEmpty) return 'Value is required';
    if (i.field == 'KPS') {
      final n = int.tryParse(v.trim());
      if (n == null || n < 0 || n > 100) return 'KPS must be 0–100';
    }
    return null;
  }
}
