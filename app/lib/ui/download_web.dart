import 'package:web/web.dart' as web;

/// Triggers a browser download and returns the file name.
Future<String> saveFile(String name, String content, String mime) async {
  final a = web.HTMLAnchorElement()
    ..href = 'data:$mime;charset=utf-8,${Uri.encodeComponent(content)}'
    ..download = name;
  web.document.body!.append(a);
  a.click();
  a.remove();
  return name;
}
