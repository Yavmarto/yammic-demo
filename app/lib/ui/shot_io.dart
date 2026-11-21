import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/rendering.dart';
import 'package:flutter/widgets.dart';

/// Demo tooling: with YAMMIC_SHOT=/path.png, render the app to a PNG after YAMMIC_SHOT_DELAY seconds, then exit.
void maybeShoot(GlobalKey boundary) {
  final out = Platform.environment['YAMMIC_SHOT'];
  if (out == null || out.isEmpty) return;
  final secs = int.tryParse(Platform.environment['YAMMIC_SHOT_DELAY'] ?? '') ?? 6;
  Future.delayed(Duration(seconds: secs), () async {
    final b = boundary.currentContext?.findRenderObject() as RenderRepaintBoundary?;
    if (b == null) exit(2);
    final img = await b.toImage(pixelRatio: 1440 / b.size.width);
    final data = await img.toByteData(format: ui.ImageByteFormat.png);
    await File('${Directory.systemTemp.path}/${out.split('/').last}').writeAsBytes(data!.buffer.asUint8List());
    exit(0);
  });
}

/// Shot mode only: lay the app out at 1440x900 even when the (virtual) display is smaller.
Widget shotFrame(Widget child) {
  final out = Platform.environment['YAMMIC_SHOT'];
  if (out == null || out.isEmpty) return child;
  return LayoutBuilder(builder: (context, _) {
    final mq = MediaQuery.of(context);
    return FittedBox(
      child: SizedBox(width: 1440, height: 900, child: MediaQuery(data: mq.copyWith(size: const Size(1440, 900)), child: child)),
    );
  });
}
