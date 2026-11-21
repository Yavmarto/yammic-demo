import 'dart:io';

/// Saves to ~/Downloads and returns the path.
Future<String> saveFile(String name, String content, String mime) async {
  final dir = Directory('${Platform.environment['HOME'] ?? '.'}/Downloads');
  if (!dir.existsSync()) dir.createSync(recursive: true);
  final f = File('${dir.path}/$name');
  await f.writeAsString(content);
  return f.path;
}
