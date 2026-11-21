// Dart models = the JSON schema contract for assets/data/*.json (synthetic data only).
// Files: dashboard.json -> Dashboard, participants.json -> {"participants":[Participant]},
// extractions.json -> {"extractions":[AiExtraction]}. See deliverables/demo_tech_spec.md.

Map<String, dynamic> _m(Object? o) => o as Map<String, dynamic>;
List<T> _l<T>(Object? o, T Function(Map<String, dynamic>) f) =>
    ((o ?? const []) as List).map((e) => f(_m(e))).toList();

class Dashboard {
  final List<Study> studies;
  final List<Site> sites;
  final List<Milestone> milestones;
  final List<Alert> alerts;
  final List<StudyTask> tasks;
  Dashboard.fromJson(Map<String, dynamic> j)
      : studies = _l(j['studies'], Study.fromJson),
        sites = _l(j['sites'], Site.fromJson),
        milestones = _l(j['milestones'], Milestone.fromJson),
        alerts = _l(j['alerts'], Alert.fromJson),
        tasks = _l(j['tasks'], StudyTask.fromJson);
}

class Study {
  final String id, title, phase;
  final int target, enrolled;
  final double completeness; // 0..1 eCRF completeness
  Study.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        title = j['title'],
        phase = j['phase'] ?? '',
        target = j['target'],
        enrolled = j['enrolled'],
        completeness = (j['completeness'] as num).toDouble();
}

class Site {
  final String id, name, studyId;
  final int target, enrolled, openQueries;
  Site.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        name = j['name'],
        studyId = j['studyId'],
        target = j['target'],
        enrolled = j['enrolled'],
        openQueries = j['openQueries'] ?? 0;
}

class Milestone {
  final String studyId, name, date; // date: ISO yyyy-MM-dd
  final bool done;
  Milestone.fromJson(Map<String, dynamic> j)
      : studyId = j['studyId'],
        name = j['name'],
        date = j['date'],
        done = j['done'] ?? false;
}

class Alert {
  final String studyId, severity, message; // severity: info|warning|critical
  Alert.fromJson(Map<String, dynamic> j)
      : studyId = j['studyId'],
        severity = j['severity'],
        message = j['message'];
}

class StudyTask {
  final String studyId, title, due, assignee;
  final String? participantId;
  StudyTask.fromJson(Map<String, dynamic> j)
      : studyId = j['studyId'],
        title = j['title'],
        due = j['due'],
        assignee = j['assignee'] ?? '',
        participantId = j['participantId'];
}

class Participant {
  final String id; // pseudonymized, e.g. "SYN-0001"
  final String studyId, siteId;
  final String status; // screening|enrolled|active|completed|withdrawn
  final int age;
  final String sex;
  final String summary; // short clinical summary (synthetic)
  final List<Visit> visits;
  final List<Ecrf> ecrfs;
  final List<QualityIssue> issues;
  final List<Treatment> treatments;
  Participant.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        studyId = j['studyId'],
        siteId = j['siteId'],
        status = j['status'],
        age = j['age'],
        sex = j['sex'],
        summary = j['summary'] ?? '',
        visits = _l(j['visits'], Visit.fromJson),
        ecrfs = _l(j['ecrfs'], Ecrf.fromJson),
        issues = _l(j['issues'], QualityIssue.fromJson),
        treatments = _l(j['treatments'], Treatment.fromJson);
}

class Visit {
  final String name, date, status, note; // status: completed|scheduled|missed
  Visit.fromJson(Map<String, dynamic> j)
      : name = j['name'],
        date = j['date'],
        status = j['status'],
        note = j['note'] ?? '';
}

class Ecrf {
  final String form, status; // status: not_started|in_progress|complete|awaiting_review
  final int completePct;
  Ecrf.fromJson(Map<String, dynamic> j)
      : form = j['form'],
        status = j['status'],
        completePct = j['completePct'] ?? 0;
}

class QualityIssue {
  final String severity, message, field; // severity: low|medium|high
  QualityIssue.fromJson(Map<String, dynamic> j)
      : severity = j['severity'],
        message = j['message'],
        field = j['field'] ?? '';
}

class Treatment {
  final String name, dose, start;
  final String? end;
  Treatment.fromJson(Map<String, dynamic> j)
      : name = j['name'],
        dose = j['dose'] ?? '',
        start = j['start'],
        end = j['end'];
}

/// AI-extracted value awaiting human review (consumed by features/review, owned by Engineer).
class AiExtraction {
  final String id, participantId, field;
  final String value; // proposed value
  final String sourceText; // synthetic source document text
  final int spanStart, spanEnd; // highlighted span in sourceText
  final double confidence; // 0..1
  final String model, promptVersion;
  AiExtraction.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        participantId = j['participantId'],
        field = j['field'],
        value = j['value'],
        sourceText = j['sourceText'],
        spanStart = j['spanStart'],
        spanEnd = j['spanEnd'],
        confidence = (j['confidence'] as num).toDouble(),
        model = j['model'],
        promptVersion = j['promptVersion'];
}

enum EventSource { ai, human }

/// Append-only audit event. Written by the review screen via AppState.audit.record().
class AuditEvent {
  final String actor, action, field; // action e.g. accept|correct|reject|extract
  final String? before, after, model, promptVersion;
  final EventSource source;
  final DateTime timestamp;
  const AuditEvent({
    required this.actor,
    required this.action,
    required this.field,
    this.before,
    this.after,
    required this.source,
    this.model,
    this.promptVersion,
    required this.timestamp,
  });
}
