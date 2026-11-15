/// Security & compliance state provider.
library;

import 'package:flutter/foundation.dart';
import 'package:cognithor_ui/services/api_client.dart';

class SecurityProvider extends ChangeNotifier {
  ApiClient? _api;

  void setApi(ApiClient? api) {
    _api = api;
  }

  Map<String, dynamic>? roles;
  Map<String, dynamic>? complianceReport;
  Map<String, dynamic>? complianceStats;
  Map<String, dynamic>? decisions;
  Map<String, dynamic>? remediations;
  Map<String, dynamic>? redteamStatus;
  List<dynamic> auditEntries = [];
  Map<String, dynamic>? authStats;
  bool isLoading = false;
  String? error;

  /// Tracks partial failures when loading multiple endpoints.
  final List<String> _partialErrors = [];

  /// Returns a combined error message when some endpoints succeed and others
  /// fail, or null when everything loaded cleanly.
  String? get partialError =>
      _partialErrors.isEmpty ? null : _partialErrors.join('; ');

  Future<void> loadRoles() async {
    if (_api == null) return;
    isLoading = true;
    notifyListeners();
    try {
      roles = await _api!.getRbacRoles();
      error = null;
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> loadComplianceReport() async {
    if (_api == null) return;
    isLoading = true;
    notifyListeners();
    try {
      complianceReport = await _api!.getComplianceReport();
      error = null;
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> loadComplianceStats() async {
    if (_api == null) return;
    isLoading = true;
    notifyListeners();
    try {
      complianceStats = await _api!.getComplianceStats();
      error = null;
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> loadDecisions() async {
    if (_api == null) return;
    isLoading = true;
    notifyListeners();
    try {
      decisions = await _api!.getComplianceDecisions();
      error = null;
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> loadRemediations() async {
    if (_api == null) return;
    isLoading = true;
    notifyListeners();
    try {
      remediations = await _api!.getComplianceRemediations();
      error = null;
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> loadRedteamStatus() async {
    if (_api == null) return;
    isLoading = true;
    notifyListeners();
    try {
      redteamStatus = await _api!.getRedteamStatus();
      error = null;
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> runRedteamScan(Map<String, dynamic> policy) async {
    if (_api == null) return;
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      await _api!.runRedteamScan(policy);
      await loadRedteamStatus();
    } catch (e) {
      error = e.toString();
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadAudit({String? action, String? severity}) async {
    if (_api == null) return;
    isLoading = true;
    notifyListeners();
    try {
      final data = await _api!.getMonitoringAudit(
        action: action,
        severity: severity,
      );
      auditEntries = data['entries'] is List ? data['entries'] as List : [];
      error = null;
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> loadAuthStats() async {
    if (_api == null) return;
    isLoading = true;
    notifyListeners();
    try {
      authStats = await _api!.getAuthStats();
      error = null;
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  /// Load all security data independently. Partial failures are tracked
  /// so the UI can show "partial data" when some endpoints succeed.
  Future<void> loadAll() async {
    if (_api == null) return;
    isLoading = true;
    _partialErrors.clear();
    error = null;
    notifyListeners();

    Future<void> safe(String label, Future<void> Function() fn) async {
      try {
        await fn();
      } catch (e) {
        _partialErrors.add('$label: $e');
      }
    }

    await Future.wait([
      safe('compliance', () async {
        complianceStats = await _api!.getComplianceStats();
      }),
      safe('remediations', () async {
        remediations = await _api!.getComplianceRemediations();
      }),
      safe('report', () async {
        complianceReport = await _api!.getComplianceReport();
      }),
      safe('roles', () async {
        roles = await _api!.getRbacRoles();
      }),
      safe('auth', () async {
        authStats = await _api!.getAuthStats();
      }),
      safe('redteam', () async {
        redteamStatus = await _api!.getRedteamStatus();
      }),
      safe('audit', () async {
        final data = await _api!.getMonitoringAudit();
        auditEntries = data['entries'] is List ? data['entries'] as List : [];
      }),
    ]);

    if (_partialErrors.isNotEmpty && _partialErrors.length == 7) {
      // All endpoints failed
      error = _partialErrors.first;
    } else if (_partialErrors.isNotEmpty) {
      // Some succeeded, some failed -- keep partial error for UI
      error = partialError;
    }

    isLoading = false;
    notifyListeners();
  }
}
