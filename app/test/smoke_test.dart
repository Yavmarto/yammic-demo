import 'package:flutter_test/flutter_test.dart';
import 'package:yammic_demo/data/audit_store.dart';
import 'package:yammic_demo/models/models.dart';

void main() {
  test('audit store is append-only and stamps events', () {
    final s = AuditStore();
    s.record(actor: 'a', action: 'accept', field: 'f', source: EventSource.human);
    expect(s.events.length, 1);
    expect(() => s.events.add(s.events.first), throwsUnsupportedError);
  });
}
