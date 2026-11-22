// Yamicc visual direction v2 - copy-ready theme extension.
// Target: Flutter 3.47+, zeta_flutter 1.4.5, zeta_flutter_theme 1.3.0.
//
// Usage:
//   ZetaProvider(
//     initialThemeMode: ThemeMode.light,
//     initialContrast: ZetaContrast.aa,
//     initialRounded: true,
//     builder: (context, light, dark, mode) => MaterialApp(
//       theme: buildYamiccTheme(light),
//       themeMode: ThemeMode.light,
//       ...
//     ),
//   )
//
// Zeta remains the base. AppColors / AppStatusColors / AppType are the product layer.
// Do not fork ZetaColors. Use Zeta.of(context).colors for Zeta components and
// AppColors.of(context) for Yamicc surfaces.

import 'package:flutter/material.dart';

const String kYamiccFontFamily = 'packages/zeta_flutter_theme/IBMPlexSans';

@immutable
class StatePalette {
  final Color surface;
  final Color border;
  final Color ink;
  final bool dashed;

  const StatePalette({
    required this.surface,
    required this.border,
    required this.ink,
    this.dashed = false,
  });

  static StatePalette lerp(StatePalette a, StatePalette b, double t) => StatePalette(
        surface: Color.lerp(a.surface, b.surface, t)!,
        border: Color.lerp(a.border, b.border, t)!,
        ink: Color.lerp(a.ink, b.ink, t)!,
        dashed: t < 0.5 ? a.dashed : b.dashed,
      );
}

@immutable
class AppColors extends ThemeExtension<AppColors> {
  final Color canvas;
  final Color surface;
  final Color surfaceSunken;
  final Color surfaceHover;
  final Color surfaceSelected;
  final Color line;
  final Color lineStrong;
  final Color inputLine;
  final Color ink;
  final Color ink2;
  final Color ink3;
  final Color accent;
  final Color accentInk;
  final Color accentSoft;
  final Color focus;
  final Color brandPanel;
  final Color brandPanelInk;
  final Color brandPanelMuted;

  const AppColors({
    required this.canvas,
    required this.surface,
    required this.surfaceSunken,
    required this.surfaceHover,
    required this.surfaceSelected,
    required this.line,
    required this.lineStrong,
    required this.inputLine,
    required this.ink,
    required this.ink2,
    required this.ink3,
    required this.accent,
    required this.accentInk,
    required this.accentSoft,
    required this.focus,
    required this.brandPanel,
    required this.brandPanelInk,
    required this.brandPanelMuted,
  });

  static const AppColors light = AppColors(
    canvas: Color(0xFFF3F6FA),
    surface: Color(0xFFFFFFFF),
    surfaceSunken: Color(0xFFEEF2F7),
    surfaceHover: Color(0xFFF3F6FA),
    surfaceSelected: Color(0xFFF1F8FF),
    line: Color(0xFFE4E9F0),
    lineStrong: Color(0xFFCED2DB),
    inputLine: Color(0xFF8A94A6),
    ink: Color(0xFF1D1E23),
    ink2: Color(0xFF545963),
    ink3: Color(0xFF667085),
    accent: Color(0xFF0073E6),
    accentInk: Color(0xFF005BB8),
    accentSoft: Color(0xFFF1F8FF),
    focus: Color(0xFF005BB8),
    brandPanel: Color(0xFF0E1B2C),
    brandPanelInk: Color(0xFFFFFFFF),
    brandPanelMuted: Color(0xFF9FB3C8),
  );

  static AppColors of(BuildContext context) =>
      Theme.of(context).extension<AppColors>() ?? AppColors.light;

  @override
  AppColors copyWith({
    Color? canvas,
    Color? surface,
    Color? surfaceSunken,
    Color? surfaceHover,
    Color? surfaceSelected,
    Color? line,
    Color? lineStrong,
    Color? inputLine,
    Color? ink,
    Color? ink2,
    Color? ink3,
    Color? accent,
    Color? accentInk,
    Color? accentSoft,
    Color? focus,
    Color? brandPanel,
    Color? brandPanelInk,
    Color? brandPanelMuted,
  }) =>
      AppColors(
        canvas: canvas ?? this.canvas,
        surface: surface ?? this.surface,
        surfaceSunken: surfaceSunken ?? this.surfaceSunken,
        surfaceHover: surfaceHover ?? this.surfaceHover,
        surfaceSelected: surfaceSelected ?? this.surfaceSelected,
        line: line ?? this.line,
        lineStrong: lineStrong ?? this.lineStrong,
        inputLine: inputLine ?? this.inputLine,
        ink: ink ?? this.ink,
        ink2: ink2 ?? this.ink2,
        ink3: ink3 ?? this.ink3,
        accent: accent ?? this.accent,
        accentInk: accentInk ?? this.accentInk,
        accentSoft: accentSoft ?? this.accentSoft,
        focus: focus ?? this.focus,
        brandPanel: brandPanel ?? this.brandPanel,
        brandPanelInk: brandPanelInk ?? this.brandPanelInk,
        brandPanelMuted: brandPanelMuted ?? this.brandPanelMuted,
      );

  @override
  AppColors lerp(ThemeExtension<AppColors>? other, double t) {
    if (other is! AppColors) return this;
    return AppColors(
      canvas: Color.lerp(canvas, other.canvas, t)!,
      surface: Color.lerp(surface, other.surface, t)!,
      surfaceSunken: Color.lerp(surfaceSunken, other.surfaceSunken, t)!,
      surfaceHover: Color.lerp(surfaceHover, other.surfaceHover, t)!,
      surfaceSelected: Color.lerp(surfaceSelected, other.surfaceSelected, t)!,
      line: Color.lerp(line, other.line, t)!,
      lineStrong: Color.lerp(lineStrong, other.lineStrong, t)!,
      inputLine: Color.lerp(inputLine, other.inputLine, t)!,
      ink: Color.lerp(ink, other.ink, t)!,
      ink2: Color.lerp(ink2, other.ink2, t)!,
      ink3: Color.lerp(ink3, other.ink3, t)!,
      accent: Color.lerp(accent, other.accent, t)!,
      accentInk: Color.lerp(accentInk, other.accentInk, t)!,
      accentSoft: Color.lerp(accentSoft, other.accentSoft, t)!,
      focus: Color.lerp(focus, other.focus, t)!,
      brandPanel: Color.lerp(brandPanel, other.brandPanel, t)!,
      brandPanelInk: Color.lerp(brandPanelInk, other.brandPanelInk, t)!,
      brandPanelMuted: Color.lerp(brandPanelMuted, other.brandPanelMuted, t)!,
    );
  }
}

@immutable
class AppStatusColors extends ThemeExtension<AppStatusColors> {
  final StatePalette ai;
  final StatePalette verified;
  final StatePalette rejected;
  final StatePalette deferred;
  final StatePalette abstained;
  final StatePalette conflict;
  final StatePalette connected;
  final StatePalette syncing;
  final StatePalette offline;
  final StatePalette info;

  final Color evidence;
  final Color evidenceActive;
  final Color evidenceUnderline;

  const AppStatusColors({
    required this.ai,
    required this.verified,
    required this.rejected,
    required this.deferred,
    required this.abstained,
    required this.conflict,
    required this.connected,
    required this.syncing,
    required this.offline,
    required this.info,
    required this.evidence,
    required this.evidenceActive,
    required this.evidenceUnderline,
  });

  static const AppStatusColors light = AppStatusColors(
    ai: StatePalette(
      surface: Color(0xFFFEF2E2),
      border: Color(0xFFB26A00),
      ink: Color(0xFF6E4A00),
      dashed: true,
    ),
    verified: StatePalette(
      surface: Color(0xFFECFFF7),
      border: Color(0xFF4EA26B),
      ink: Color(0xFF0C5734),
    ),
    rejected: StatePalette(
      surface: Color(0xFFFFF0F1),
      border: Color(0xFFD70015),
      ink: Color(0xFF8F000E),
    ),
    deferred: StatePalette(
      surface: Color(0xFFF3F6FA),
      border: Color(0xFF8A94A6),
      ink: Color(0xFF3F4B58),
    ),
    abstained: StatePalette(
      surface: Color(0xFFF3F6FA),
      border: Color(0xFF8A94A6),
      ink: Color(0xFF3F4B58),
      dashed: true,
    ),
    conflict: StatePalette(
      surface: Color(0xFFFFF0F1),
      border: Color(0xFFD70015),
      ink: Color(0xFF8F000E),
    ),
    connected: StatePalette(
      surface: Color(0xFFE7F7F7),
      border: Color(0xFF1A8080),
      ink: Color(0xFF0B4F4F),
    ),
    syncing: StatePalette(
      surface: Color(0xFFFEF2E2),
      border: Color(0xFFB26A00),
      ink: Color(0xFF6E4A00),
    ),
    offline: StatePalette(
      surface: Color(0xFFF3F6FA),
      border: Color(0xFF8A94A6),
      ink: Color(0xFF3F4B58),
    ),
    info: StatePalette(
      surface: Color(0xFFF7F0FF),
      border: Color(0xFF9B71DF),
      ink: Color(0xFF4B1F8A),
    ),
    evidence: Color(0xFFFFE1A8),
    evidenceActive: Color(0xFFFFD08A),
    evidenceUnderline: Color(0xFF8A5A00),
  );

  static AppStatusColors of(BuildContext context) =>
      Theme.of(context).extension<AppStatusColors>() ?? AppStatusColors.light;

  @override
  AppStatusColors copyWith({
    StatePalette? ai,
    StatePalette? verified,
    StatePalette? rejected,
    StatePalette? deferred,
    StatePalette? abstained,
    StatePalette? conflict,
    StatePalette? connected,
    StatePalette? syncing,
    StatePalette? offline,
    StatePalette? info,
    Color? evidence,
    Color? evidenceActive,
    Color? evidenceUnderline,
  }) =>
      AppStatusColors(
        ai: ai ?? this.ai,
        verified: verified ?? this.verified,
        rejected: rejected ?? this.rejected,
        deferred: deferred ?? this.deferred,
        abstained: abstained ?? this.abstained,
        conflict: conflict ?? this.conflict,
        connected: connected ?? this.connected,
        syncing: syncing ?? this.syncing,
        offline: offline ?? this.offline,
        info: info ?? this.info,
        evidence: evidence ?? this.evidence,
        evidenceActive: evidenceActive ?? this.evidenceActive,
        evidenceUnderline: evidenceUnderline ?? this.evidenceUnderline,
      );

  @override
  AppStatusColors lerp(ThemeExtension<AppStatusColors>? other, double t) {
    if (other is! AppStatusColors) return this;
    return AppStatusColors(
      ai: StatePalette.lerp(ai, other.ai, t),
      verified: StatePalette.lerp(verified, other.verified, t),
      rejected: StatePalette.lerp(rejected, other.rejected, t),
      deferred: StatePalette.lerp(deferred, other.deferred, t),
      abstained: StatePalette.lerp(abstained, other.abstained, t),
      conflict: StatePalette.lerp(conflict, other.conflict, t),
      connected: StatePalette.lerp(connected, other.connected, t),
      syncing: StatePalette.lerp(syncing, other.syncing, t),
      offline: StatePalette.lerp(offline, other.offline, t),
      info: StatePalette.lerp(info, other.info, t),
      evidence: Color.lerp(evidence, other.evidence, t)!,
      evidenceActive: Color.lerp(evidenceActive, other.evidenceActive, t)!,
      evidenceUnderline: Color.lerp(evidenceUnderline, other.evidenceUnderline, t)!,
    );
  }
}

/// Zeta ships IBM Plex Sans at 300 / 400 / 500 only. Do not use 600 or 700.
abstract final class AppType {
  static const display = TextStyle(
    fontFamily: kYamiccFontFamily,
    fontSize: 32,
    height: 40 / 32,
    fontWeight: FontWeight.w500,
    letterSpacing: -0.4,
  );

  static const h1 = TextStyle(
    fontFamily: kYamiccFontFamily,
    fontSize: 24,
    height: 32 / 24,
    fontWeight: FontWeight.w500,
    letterSpacing: -0.2,
  );

  static const h2 = TextStyle(
    fontFamily: kYamiccFontFamily,
    fontSize: 20,
    height: 28 / 20,
    fontWeight: FontWeight.w500,
  );

  static const h3 = TextStyle(
    fontFamily: kYamiccFontFamily,
    fontSize: 16,
    height: 24 / 16,
    fontWeight: FontWeight.w500,
  );

  static const body = TextStyle(
    fontFamily: kYamiccFontFamily,
    fontSize: 14,
    height: 21 / 14,
    fontWeight: FontWeight.w400,
  );

  static const bodyLarge = TextStyle(
    fontFamily: kYamiccFontFamily,
    fontSize: 15,
    height: 26 / 15,
    fontWeight: FontWeight.w400,
  );

  static const small = TextStyle(
    fontFamily: kYamiccFontFamily,
    fontSize: 12.5,
    height: 18 / 12.5,
    fontWeight: FontWeight.w400,
  );

  static const label = TextStyle(
    fontFamily: kYamiccFontFamily,
    fontSize: 11,
    height: 16 / 11,
    fontWeight: FontWeight.w500,
    letterSpacing: 0.88,
  );

  static const numeric = TextStyle(
    fontFamily: kYamiccFontFamily,
    fontSize: 14,
    height: 20 / 14,
    fontWeight: FontWeight.w500,
    fontFeatures: [FontFeature.tabularFigures()],
  );

  static const metric = TextStyle(
    fontFamily: kYamiccFontFamily,
    fontSize: 28,
    height: 34 / 28,
    fontWeight: FontWeight.w500,
    letterSpacing: -0.3,
    fontFeatures: [FontFeature.tabularFigures()],
  );

  static const mono = TextStyle(
    fontFamily: 'monospace',
    fontSize: 12,
    height: 18 / 12,
    fontWeight: FontWeight.w400,
    fontFeatures: [FontFeature.tabularFigures()],
  );
}

abstract final class AppSpace {
  static const s1 = 4.0;
  static const s2 = 8.0;
  static const s3 = 12.0;
  static const s4 = 16.0;
  static const s6 = 24.0;
  static const s8 = 32.0;
  static const s12 = 48.0;
  static const s16 = 64.0;

  static const page1440 = 24.0;
  static const page1280 = 20.0;
  static const panel = 20.0;
  static const panelLarge = 24.0;
  static const section = 32.0;
  static const panelGap = 16.0;
  static const rowGap = 8.0;
  static const tableRow = 44.0;
  static const tableRowDense = 40.0;
  static const topBar = 56.0;
  static const banner = 28.0;
  static const offlineBanner = 32.0;
  static const sidebarExpanded = 232.0;
  static const sidebarCollapsed = 72.0;
  static const touch = 40.0;
  static const iconButton = 32.0;
}

abstract final class AppRadii {
  static const control = 8.0;
  static const panel = 12.0;
  static const dialog = 16.0;
  static const pill = 999.0;
  static const evidence = 3.0;
}

abstract final class AppMotion {
  static const fast = Duration(milliseconds: 120);
  static const base = Duration(milliseconds: 180);
  static const slow = Duration(milliseconds: 240);
  static const scroll = Duration(milliseconds: 200);
  static const exit = Duration(milliseconds: 90);
  static const progress = Duration(milliseconds: 420);
  static const skeleton = Duration(milliseconds: 1200);

  static const curve = Curves.easeOutCubic;
  static const exitCurve = Curves.easeInCubic;
}

const List<BoxShadow> kOverlayShadow = [
  BoxShadow(color: Color(0x1A101828), blurRadius: 24, offset: Offset(0, 8)),
  BoxShadow(color: Color(0x0F101828), blurRadius: 6, offset: Offset(0, 2)),
];

/// Layer the Yamicc product look over the Zeta Material theme.
ThemeData buildYamiccTheme(ThemeData base) {
  const c = AppColors.light;
  final scheme = base.colorScheme.copyWith(
    primary: c.accent,
    onPrimary: Colors.white,
    primaryContainer: c.accentSoft,
    onPrimaryContainer: c.accentInk,
    surface: c.surface,
    onSurface: c.ink,
    onSurfaceVariant: c.ink2,
    outline: c.lineStrong,
    outlineVariant: c.line,
    error: const Color(0xFFD70015),
    onError: Colors.white,
    errorContainer: const Color(0xFFFFF0F1),
    onErrorContainer: const Color(0xFF8F000E),
  );

  final textTheme = base.textTheme
      .apply(bodyColor: c.ink, displayColor: c.ink)
      .copyWith(
        headlineLarge: AppType.h1.copyWith(color: c.ink),
        headlineMedium: AppType.h2.copyWith(color: c.ink),
        headlineSmall: AppType.h3.copyWith(color: c.ink),
        titleLarge: AppType.h2.copyWith(color: c.ink),
        titleMedium: AppType.h3.copyWith(color: c.ink),
        titleSmall: AppType.label.copyWith(color: c.ink3),
        bodyLarge: AppType.bodyLarge.copyWith(color: c.ink),
        bodyMedium: AppType.body.copyWith(color: c.ink),
        bodySmall: AppType.small.copyWith(color: c.ink2),
        labelLarge: AppType.body.copyWith(
          color: c.ink,
          fontWeight: FontWeight.w500,
        ),
        labelMedium: AppType.small.copyWith(
          color: c.ink2,
          fontWeight: FontWeight.w500,
        ),
        labelSmall: AppType.label.copyWith(color: c.ink3),
      );

  OutlineInputBorder border(Color color, [double width = 1]) => OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadii.control),
        borderSide: BorderSide(color: color, width: width),
      );

  return base.copyWith(
    colorScheme: scheme,
    scaffoldBackgroundColor: c.canvas,
    canvasColor: c.canvas,
    dividerColor: c.line,
    dividerTheme: const DividerThemeData(
      color: Color(0xFFE4E9F0),
      thickness: 1,
      space: 1,
    ),
    textTheme: textTheme,
    cardTheme: const CardThemeData(
      elevation: 0,
      margin: EdgeInsets.zero,
      color: Color(0xFFFFFFFF),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.all(Radius.circular(AppRadii.panel)),
        side: BorderSide(color: Color(0xFFE4E9F0)),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: c.surface,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadii.dialog),
        side: BorderSide(color: c.line),
      ),
      titleTextStyle: AppType.h2.copyWith(color: c.ink),
      contentTextStyle: AppType.body.copyWith(color: c.ink),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: c.accent,
        foregroundColor: Colors.white,
        disabledBackgroundColor: c.line,
        disabledForegroundColor: c.ink3,
        minimumSize: const Size(0, AppSpace.touch),
        padding: const EdgeInsets.symmetric(horizontal: AppSpace.s4),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.control),
        ),
        textStyle: AppType.body.copyWith(
          color: Colors.white,
          fontWeight: FontWeight.w500,
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: c.ink,
        disabledForegroundColor: c.ink3,
        minimumSize: const Size(0, AppSpace.touch),
        padding: const EdgeInsets.symmetric(horizontal: AppSpace.s4),
        side: BorderSide(color: c.lineStrong),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.control),
        ),
        textStyle: AppType.body.copyWith(
          color: c.ink,
          fontWeight: FontWeight.w500,
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: c.accentInk,
        disabledForegroundColor: c.ink3,
        minimumSize: const Size(0, AppSpace.touch),
        padding: const EdgeInsets.symmetric(horizontal: AppSpace.s2),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.control),
        ),
        textStyle: AppType.body.copyWith(
          color: c.accentInk,
          fontWeight: FontWeight.w500,
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      isDense: true,
      filled: true,
      fillColor: c.surface,
      contentPadding: const EdgeInsets.symmetric(
        horizontal: AppSpace.s3,
        vertical: 11,
      ),
      labelStyle: AppType.body.copyWith(color: c.ink2),
      hintStyle: AppType.body.copyWith(color: c.ink3),
      helperStyle: AppType.small.copyWith(color: c.ink3),
      errorStyle: AppType.small.copyWith(color: const Color(0xFF8F000E)),
      border: border(c.inputLine),
      enabledBorder: border(c.inputLine),
      focusedBorder: border(c.accent, 2),
      errorBorder: border(const Color(0xFFD70015)),
      focusedErrorBorder: border(const Color(0xFFD70015), 2),
      disabledBorder: border(c.line),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: c.ink,
      contentTextStyle: AppType.body.copyWith(color: Colors.white),
      width: 420,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadii.control),
      ),
    ),
    tooltipTheme: TooltipThemeData(
      decoration: BoxDecoration(
        color: c.ink,
        borderRadius: BorderRadius.circular(6),
      ),
      textStyle: AppType.small.copyWith(color: Colors.white),
      waitDuration: const Duration(milliseconds: 350),
    ),
    focusColor: c.focus.withValues(alpha: 0.12),
    hoverColor: c.surfaceHover,
    splashColor: Colors.transparent,
    highlightColor: Colors.transparent,
    extensions: <ThemeExtension<dynamic>>[
      ...base.extensions.values,
      AppColors.light,
      AppStatusColors.light,
    ],
  );
}
