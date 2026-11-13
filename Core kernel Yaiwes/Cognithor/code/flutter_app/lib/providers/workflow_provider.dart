/// Workflow state provider.
library;

import 'package:flutter/foundation.dart';
import 'package:cognithor_ui/services/api_client.dart';

class WorkflowProvider extends ChangeNotifier {
  ApiClient? _api;

  void setApi(ApiClient? api) {
    _api = api;
  }

  List<dynamic> categories = [];
  bool isLoading = false;
  String? error;

  Future<void> loadCategories() async {
    if (_api == null) return;
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      final data = await _api!.getWorkflowCategories();
      categories = data['categories'] as List<dynamic>? ?? [];
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> startWorkflow(String templateId) async {
    if (_api == null) return;
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      await _api!.startWorkflow(templateId);
    } catch (e) {
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }
}
