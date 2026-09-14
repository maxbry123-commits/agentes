import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:cognithor_ui/theme/cognithor_theme.dart';

class ThemeProvider extends ChangeNotifier {
  ThemeProvider() {
    _load();
  }

  ThemeMode _mode = ThemeMode.dark;
  ThemeMode get mode => _mode;
  bool get isDark => _mode == ThemeMode.dark;

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final stored = prefs.getString('theme_mode');
    if (stored == 'light') {
      _mode = ThemeMode.light;
      CognithorTheme.setDarkMode(false);
      notifyListeners();
    }
  }

  Future<void> toggle() async {
    _mode = isDark ? ThemeMode.light : ThemeMode.dark;
    CognithorTheme.setDarkMode(_mode == ThemeMode.dark);
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('theme_mode', isDark ? 'dark' : 'light');
  }
}
