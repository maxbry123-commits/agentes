import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LocaleProvider extends ChangeNotifier {
  LocaleProvider() {
    _load();
  }

  static const supportedCodes = ['en', 'de', 'zh', 'ar'];

  Locale _locale = const Locale('en');
  Locale get locale => _locale;

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString('app_locale');
    if (saved != null && supportedCodes.contains(saved)) {
      _locale = Locale(saved);
      notifyListeners();
      return;
    }

    // First launch: detect system language
    final systemCode = ui.PlatformDispatcher.instance.locale.languageCode;
    final detected = supportedCodes.contains(systemCode) ? systemCode : 'en';
    _locale = Locale(detected);
    await prefs.setString('app_locale', detected);
    notifyListeners();
  }

  Future<void> setLocale(String code) async {
    if (!supportedCodes.contains(code)) return;
    _locale = Locale(code);
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('app_locale', code);
  }

  /// Sync from ConfigProvider language field
  void syncFromConfig(String? language) {
    if (language != null &&
        supportedCodes.contains(language) &&
        language != _locale.languageCode) {
      setLocale(language);
    }
  }
}
