import 'package:flutter/material.dart';
import '../api/api.dart';

enum Conn { online, offline }

/// Who is signed in, which backend we talk to, and whether we fell back to the snapshot.
class Session extends ChangeNotifier {
  final HttpApi http;
  final Api offlineApi;
  Session({HttpApi? http, Api? offline}) : http = http ?? HttpApi(), offlineApi = offline ?? OfflineApi();

  Map<String, dynamic>? user;
  Conn conn = Conn.online;
  int? latencyMs;
  int? pending; // AI proposals awaiting review (sidebar badge)
  void setPending(int n) {
    if (pending == n) return;
    pending = n;
    notifyListeners();
  }

  /// Demo clock is fixed (D7b §3.8): never DateTime.now() in the UI.
  static final demoToday = DateTime(2026, 11, 23);

  bool get signedIn => user != null;
  bool get offline => conn == Conn.offline;
  String get role => (user?['role'] ?? 'nurse') as String;
  String get userName => (user?['name'] ?? '') as String;
  String get username => (user?['username'] ?? '') as String;
  bool get isMonitor => role == 'monitor';

  /// Reads go to the live backend, or the snapshot when offline.
  Api get api => offline ? offlineApi : http;

  /// Run a read; if the live backend is unreachable, switch to the snapshot and retry once.
  Future<T> run<T>(Future<T> Function(Api a) f) async {
    try {
      return await f(api);
    } on Unreachable {
      if (offline) rethrow;
      markOffline();
      return f(offlineApi);
    }
  }

  /// Writes are blocked offline and for the monitor role.
  bool get canWrite => !offline && !isMonitor;
  bool get isPi => role == 'pi';
  String? get writeBlockedReason =>
      offline ? 'Offline snapshot is read-only.' : isMonitor ? 'Monitor role is read-only in this demo.' : null;

  Future<bool> ping() async {
    final sw = Stopwatch()..start();
    try {
      await http.get('/health');
      latencyMs = sw.elapsedMilliseconds;
      if (offline) conn = Conn.online;
      notifyListeners();
      return true;
    } catch (_) {
      return false;
    }
  }

  /// Throws ApiException on bad credentials; goes offline (and signs in as a read-only viewer) if unreachable.
  Future<void> login(String username, String password, {String? roleHint}) async {
    try {
      final r = await http.post('/auth/login', {'username': username, 'password': password}) as Map;
      http.token = r['accessToken'] as String;
      user = Map<String, dynamic>.from(r['user']);
      conn = Conn.online;
      await ping();
    } on Unreachable {
      conn = Conn.offline;
      user = {'username': username, 'role': roleHint ?? username, 'name': 'Offline viewer'};
    }
    notifyListeners();
  }

  void logout() {
    http.token = null;
    user = null;
    pending = null;
    conn = Conn.online;
    notifyListeners();
  }

  /// Called by data screens when a request fails with Unreachable.
  void markOffline() {
    if (offline) return;
    conn = Conn.offline;
    notifyListeners();
  }

  Future<void> retryOnline() async {
    if (await ping() && http.token == null) {
      // signed in offline: need a real login against the backend
      logout();
    } else {
      notifyListeners();
    }
  }
}

class SessionScope extends InheritedNotifier<Session> {
  const SessionScope({super.key, required Session session, required super.child}) : super(notifier: session);
  static Session of(BuildContext c) => c.dependOnInheritedWidgetOfExactType<SessionScope>()!.notifier!;
  static Session read(BuildContext c) => c.getInheritedWidgetOfExactType<SessionScope>()!.notifier!;
}
