import 'dart:io';

/// Launch-time env var (desktop only): YAMICC_ROLE, YAMICC_ROUTE, YAMICC_API.
String envVar(String name) => Platform.environment[name] ?? '';
