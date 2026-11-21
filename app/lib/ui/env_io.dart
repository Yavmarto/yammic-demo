import 'dart:io';

/// Launch-time env var (desktop only): YAMMIC_ROLE, YAMMIC_ROUTE, YAMMIC_API.
String envVar(String name) => Platform.environment[name] ?? '';
