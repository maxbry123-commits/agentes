/// Memory & knowledge graph state provider.
library;

import 'package:flutter/foundation.dart';
import 'package:cognithor_ui/services/api_client.dart';

class MemoryProvider extends ChangeNotifier {
  ApiClient? _api;

  void setApi(ApiClient? api) {
    _api = api;
  }

  Map<String, dynamic>? graphStats;
  List<dynamic> entities = [];
  Map<String, dynamic>? hygieneStats;
  List<dynamic> quarantined = [];
  Map<String, dynamic>? explainabilityStats;
  List<dynamic> trails = [];
  List<dynamic> lowTrustTrails = [];
  bool isLoading = false;
  String? error;

  Future<void> loadGraphStats() async {
    if (_api == null) return;
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      graphStats = await _api!.getMemoryGraphStats();
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> loadEntities() async {
    if (_api == null) return;
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      final data = await _api!.getMemoryGraphEntities();
      entities = data['entities'] as List<dynamic>? ?? [];
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> loadHygieneStats() async {
    if (_api == null) return;
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      hygieneStats = await _api!.getHygieneStats();
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> scanHygiene() async {
    if (_api == null) return;
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      await _api!.scanHygiene();
      await loadHygieneStats();
    } catch (e) {
      error = e.toString();
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadQuarantine() async {
    if (_api == null) return;
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      final data = await _api!.getQuarantine();
      quarantined = data['items'] as List<dynamic>? ?? [];
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> loadExplainability() async {
    if (_api == null) return;
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      explainabilityStats = await _api!.getExplainabilityStats();
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> loadTrails() async {
    if (_api == null) return;
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      final data = await _api!.getExplainabilityTrails();
      trails = data['trails'] as List<dynamic>? ?? [];
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> loadLowTrustTrails() async {
    if (_api == null) return;
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      final data = await _api!.getLowTrustTrails();
      lowTrustTrails = data['trails'] as List<dynamic>? ?? [];
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }
}
