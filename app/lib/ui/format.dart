const _mon = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/// '2026-11-23' or ISO timestamp -> '23 Nov 2026'.
String fmtDate(Object? v) {
  final d = v == null ? null : DateTime.tryParse('$v');
  return d == null ? '—' : '${d.day} ${_mon[d.month - 1]} ${d.year}';
}

/// ISO timestamp -> '14:04' (UTC kept as-is; demo shows CET in detail views).
String fmtTime(Object? v) {
  final d = v == null ? null : DateTime.tryParse('$v')?.toLocal();
  return d == null ? '' : '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
}

String fmtDateTime(Object? v) => '${fmtDate(v)} ${fmtTime(v)}'.trim();

String pct(num? v) => v == null ? '—' : '${(v * 100).round()}%';

String short(String? h, [int n = 8]) => h == null || h.length <= n * 2 + 3 ? (h ?? '') : '0x${h.substring(0, n)}…${h.substring(h.length - 4)}';
