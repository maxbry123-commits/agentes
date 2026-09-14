/// Manages connection to Cognithor backend over Tailscale or local network.
///
/// This is a lower-level helper used alongside [ConnectionProvider] for
/// discovery and reachability checks without requiring the full provider
/// lifecycle.
library;

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ConnectionManager {
  ConnectionManager({required this.prefs});

  final SharedPreferences prefs;

  static const _serverUrlKey = 'cognithor_server_url';
  static const _defaultUrl = 'http://localhost:8741';

  String get serverUrl => prefs.getString(_serverUrlKey) ?? _defaultUrl;

  Future<void> setServerUrl(String url) async {
    await prefs.setString(
      _serverUrlKey,
      url.trimRight().replaceAll(RegExp(r'/+$'), ''),
    );
  }

  /// Try to discover Cognithor on common addresses.
  Future<String?> autoDiscover() async {
    final candidates = [
      'http://localhost:8741', // Same device
      'http://192.168.1.100:8741', // Common LAN
      // Tailscale: user configures manually
    ];

    for (final url in candidates) {
      try {
        final response = await http
            .get(Uri.parse('$url/api/v1/health'))
            .timeout(const Duration(seconds: 2));
        if (response.statusCode == 200) return url;
      } catch (_) {}
    }
    return null;
  }

  /// Check if backend is reachable.
  Future<bool> isConnected() async {
    try {
      final response = await http
          .get(Uri.parse('$serverUrl/api/v1/health'))
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
