import 'package:flutter/material.dart';

/// Design tokens. Cool-tinted neutrals, one accent, semantic state colours.
/// Light only: clinical coordinators work at a desk in daylight for long review sessions.
class K {
  static const bg = Color(0xFFF3F6FA);
  static const surface = Color(0xFFFFFFFF);
  static const sidebar = Color(0xFFEEF2F7);
  static const line = Color(0xFFE4E9F0);
  static const lineStrong = Color(0xFFCED2DB);
  static const ink = Color(0xFF1D1E23);
  static const ink2 = Color(0xFF545963);
  static const ink3 = Color(0xFF667085);
  static const accent = Color(0xFF0073E6);
  static const accentSoft = Color(0xFFF1F8FF);

  // Semantic: AI proposal (amber, dashed), human verified (green), rejected (red), neutral.
  static const aiBg = Color(0xFFFEF2E2), aiLine = Color(0xFFB26A00), aiInk = Color(0xFF6E4A00);
  static const okBg = Color(0xFFECFFF7), okLine = Color(0xFF4EA26B), okInk = Color(0xFF0C5734);
  static const badBg = Color(0xFFFFF0F1), badLine = Color(0xFFD70015), badInk = Color(0xFF8F000E);
  static const infoBg = Color(0xFFF1F8FF), infoLine = Color(0xFF7CB4F0), infoInk = Color(0xFF005BB8);
  static const mutedBg = Color(0xFFEDF0F4), mutedLine = Color(0xFFB5BEC9), mutedInk = Color(0xFF3F4B58);

  // Spacing rhythm (not uniform on purpose).
  static const s4 = 4.0, s8 = 8.0, s12 = 12.0, s16 = 16.0, s24 = 24.0, s32 = 32.0, s48 = 48.0;

  // Type scale ~1.2. One family (Zeta's), weight carries hierarchy.
  static const display = TextStyle(fontSize: 28, height: 1.2, fontWeight: FontWeight.w500, letterSpacing: -0.4, color: ink);
  static const title = TextStyle(fontSize: 20, height: 1.3, fontWeight: FontWeight.w500, letterSpacing: -0.2, color: ink);
  static const heading = TextStyle(fontSize: 15, height: 1.4, fontWeight: FontWeight.w500, color: ink);
  static const body = TextStyle(fontSize: 14, height: 1.5, color: ink);
  static const small = TextStyle(fontSize: 12.5, height: 1.4, color: ink2);
  static const label = TextStyle(fontSize: 11, height: 1.3, fontWeight: FontWeight.w500, letterSpacing: 0.7, color: ink3);
  static const mono = TextStyle(fontSize: 12.5, height: 1.4, color: ink2, fontFeatures: [FontFeature.tabularFigures()]);

  static const teal = Color(0xFF1A8080), tealBg = Color(0xFFE7F7F7), tealInk = Color(0xFF0B4F4F);
  static const chart3 = Color(0xFF8D7400);

  static const ease = Curves.easeOutCubic;
  static const fast = Duration(milliseconds: 160);
}

/// Layers the product look over Zeta's ThemeData (Zeta stays the base).
ThemeData applyLook(ThemeData z) => z.copyWith(
      scaffoldBackgroundColor: K.bg,
      canvasColor: K.bg,
      dividerColor: K.line,
      dividerTheme: const DividerThemeData(color: K.line, thickness: 1, space: 1),
      colorScheme: z.colorScheme.copyWith(primary: K.accent, surface: K.surface),
      textTheme: z.textTheme.apply(bodyColor: K.ink, displayColor: K.ink),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: K.accent,
          foregroundColor: Colors.white,
          minimumSize: const Size(0, 40),
          padding: const EdgeInsets.symmetric(horizontal: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: K.ink,
          minimumSize: const Size(0, 40),
          side: const BorderSide(color: K.lineStrong),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: K.accent,
          minimumSize: const Size(0, 40),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        isDense: true,
        filled: true,
        fillColor: K.surface,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: K.lineStrong)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: K.lineStrong)),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: K.accent, width: 2)),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: K.ink,
        width: 420,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: K.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14), side: const BorderSide(color: K.line)),
      ),
    );
