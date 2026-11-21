import 'package:flutter/material.dart';
import 'package:zeta_flutter/zeta_flutter.dart';
import 'data/session.dart';
import 'features/ai_quality/ai_quality_screen.dart';
import 'features/audit/audit_screen.dart';
import 'features/dashboard/dashboard_screen.dart';
import 'features/export/export_screen.dart';
import 'features/integrations/integrations_screen.dart';
import 'features/login/login_screen.dart';
import 'features/participant/participant_screen.dart';
import 'features/review/review_screen.dart';
import 'shell/shell.dart';
import 'theme/tokens.dart';

void main() => runApp(DemoApp(session: Session()));

class DemoApp extends StatefulWidget {
  final Session session;
  const DemoApp({super.key, required this.session});
  @override
  State<DemoApp> createState() => _DemoAppState();
}

class _DemoAppState extends State<DemoApp> {
  final nav = GlobalKey<NavigatorState>();
  Session get session => widget.session;
  String? _who;

  @override
  void initState() {
    super.initState();
    session.addListener(_onSession);
  }

  @override
  void dispose() {
    session.removeListener(_onSession);
    super.dispose();
  }

  // Sign-in / sign-out resets the route stack (login <-> dashboard).
  void _onSession() {
    final who = session.user?['username'] as String?;
    if (who != _who) {
      _who = who;
      nav.currentState?.pushNamedAndRemoveUntil('/', (_) => false);
    }
  }

  Route<dynamic> _route(RouteSettings s) {
    final name = s.name ?? '/';
    Widget page;
    String nav = '/';
    if (!session.signedIn) {
      page = const LoginScreen();
      nav = '';
    } else if (name.startsWith('/participants/')) {
      page = ParticipantScreen(id: name.substring('/participants/'.length));
      nav = '/participants';
    } else {
      nav = name == '/login' ? '/' : name;
      page = switch (name) {
        '/participants' => const ParticipantListScreen(),
        '/review' => ReviewScreen(participantId: s.arguments as String?),
        '/audit' => const AuditScreen(),
        '/integrations' => const IntegrationsScreen(),
        '/ai-quality' => const AiQualityScreen(),
        '/export' => const ExportScreen(),
        _ => const DashboardScreen(),
      };
    }
    final body = nav.isEmpty ? page : Shell(selected: nav, child: page);
    return PageRouteBuilder(
      settings: s,
      pageBuilder: (_, _, _) => body,
      transitionDuration: const Duration(milliseconds: 120),
      reverseTransitionDuration: Duration.zero,
      transitionsBuilder: (_, a, _, c) => FadeTransition(opacity: a, child: c),
    );
  }

  @override
  Widget build(BuildContext context) => SessionScope(
        session: session,
        child: ZetaProvider(
          initialThemeMode: ThemeMode.light,
          // ponytail: fixed contrast skips Zeta's shared-preferences read at startup;
          // if that read fails, ZetaProvider throws LateInitializationError (red screen).
          initialContrast: ZetaContrast.aa,
          builder: (context, light, dark, themeMode) => MaterialApp(
            title: 'Yammic demo',
            debugShowCheckedModeBanner: false,
            theme: applyLook(light),
            darkTheme: applyLook(light), // light-only product look
            themeMode: ThemeMode.light,
            navigatorKey: nav,
            onGenerateRoute: _route,
          ),
        ),
      );
}
