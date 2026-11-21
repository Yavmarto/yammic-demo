import 'package:flutter/material.dart';
import 'package:zeta_flutter/zeta_flutter.dart';
import 'data/app_state.dart';
import 'features/audit/audit_screen.dart';
import 'features/dashboard/dashboard_screen.dart';
import 'features/participant/participant_screen.dart';
import 'features/review/review_screen.dart';
import 'shell/shell.dart';
import 'theme/tokens.dart';
import 'ui/widgets.dart';

void main() => runApp(const DemoApp());

class DemoApp extends StatefulWidget {
  const DemoApp({super.key});
  @override
  State<DemoApp> createState() => _DemoAppState();
}

class _DemoAppState extends State<DemoApp> {
  final state = AppState();
  late Future<void> loaded = state.load();

  Route<dynamic> _route(RouteSettings s) {
    final name = s.name ?? '/';
    Widget page;
    int tab = 0;
    if (name.startsWith('/participant/')) {
      page = ParticipantScreen(id: name.substring('/participant/'.length));
      tab = 1;
    } else {
      switch (name) {
        case '/participants':
          page = const ParticipantListScreen();
          tab = 1;
        case '/review':
          page = ReviewScreen(participantId: s.arguments as String?);
          tab = 2;
        case '/audit':
          page = const AuditScreen();
          tab = 3;
        default:
          page = const DashboardScreen();
      }
    }
    return PageRouteBuilder(
      settings: s,
      pageBuilder: (_, _, _) => Shell(selected: tab, child: page),
      transitionDuration: Duration.zero,
    );
  }

  @override
  Widget build(BuildContext context) => AppScope(
        state: state,
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
            builder: (context, child) => FutureBuilder<void>(
              future: loaded,
              builder: (_, snap) => snap.connectionState != ConnectionState.done
                  ? const Scaffold(body: PageSkeleton())
                  : snap.hasError
                      ? Scaffold(
                          body: ErrorState(
                            message: '${snap.error}',
                            onRetry: () => setState(() => loaded = state.load()),
                          ),
                        )
                      : child!,
            ),
            onGenerateRoute: _route,
          ),
        ),
      );
}
