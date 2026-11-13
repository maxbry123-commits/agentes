// ignore_for_file: avoid_web_libraries_in_flutter

// Web implementation: reads token from <meta name="cognithor-token"> in DOM.
import 'package:web/web.dart' as web;

String? readTokenFromMeta() {
  final meta = web.document.querySelector('meta[name="cognithor-token"]');
  return meta?.getAttribute('content');
}
