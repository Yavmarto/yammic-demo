import 'dart:convert';
import 'package:flutter/services.dart';
import '../models/models.dart';

/// Single data-access seam. W7 adds an API-backed implementation and wraps this one as offline fallback.
abstract class DemoRepository {
  Future<Dashboard> dashboard();
  Future<List<Participant>> participants();

  /// Raw extraction rows (richer than models.AiExtraction); ReviewStore wraps them.
  Future<List<Map<String, dynamic>>> extractions();
}

/// First adapter: bundled synthetic JSON under assets/data.
class JsonAssetRepository implements DemoRepository {
  final AssetBundle? bundle;
  const JsonAssetRepository([this.bundle]);

  Future<Map<String, dynamic>> _load(String f) async =>
      jsonDecode(await (bundle ?? rootBundle).loadString('assets/data/$f', cache: false)) as Map<String, dynamic>;

  @override
  Future<Dashboard> dashboard() async => Dashboard.fromJson(await _load('dashboard.json'));

  @override
  Future<List<Participant>> participants() async =>
      [for (final e in (await _load('participants.json'))['participants'] as List) Participant.fromJson(e)];

  @override
  Future<List<Map<String, dynamic>>> extractions() async =>
      [for (final e in (await _load('extractions.json'))['extractions'] as List) e as Map<String, dynamic>];
}
