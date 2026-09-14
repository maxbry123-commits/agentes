/// Voice mode state management.
///
/// Wraps [VoiceService] in a [ChangeNotifier] for Provider integration.
/// Accepts an [ApiClient] for TTS synthesis and a [sendToChat] callback
/// for forwarding recognized speech to the chat system.
library;

import 'package:flutter/foundation.dart';
import 'package:cognithor_ui/services/api_client.dart';
import 'package:cognithor_ui/services/voice_service.dart';

class VoiceProvider extends ChangeNotifier {
  VoiceProvider({this.apiClient, this.sendToChat}) {
    _service.addListener(_onServiceChanged);
  }

  /// Optional API client for TTS calls.
  ApiClient? apiClient;

  /// Optional callback invoked when a voice command is recognized
  /// (i.e. state transitions from CONVERSATION to PROCESSING).
  void Function(String text)? sendToChat;

  final VoiceService _service = VoiceService();

  VoiceState get state => _service.state;
  bool get isActive => _service.state != VoiceState.off;
  String get lastTranscript => _service.lastTranscript;
  String? get errorMessage => _service.errorMessage;

  /// Previous state, used to detect CONVERSATION -> PROCESSING transitions.
  VoiceState _prevState = VoiceState.off;

  void _onServiceChanged() {
    final current = _service.state;

    // Detect transition into PROCESSING — means user spoke a command.
    if (_prevState == VoiceState.conversation &&
        current == VoiceState.processing) {
      final text = _service.lastTranscript;
      if (text.isNotEmpty && sendToChat != null) {
        sendToChat!(text);
      }
    }

    _prevState = current;
    notifyListeners();
  }

  Future<void> toggle() async {
    if (isActive) {
      await _service.stop();
    } else {
      await _service.start();
    }
  }

  Future<void> stop() async {
    await _service.stop();
  }

  /// Synthesize speech for [text] via the API and play it back.
  ///
  /// If [api] is provided it is used; otherwise falls back to [apiClient].
  Future<void> speakResponse(String text, [ApiClient? api]) async {
    final client = api ?? apiClient;
    if (client == null) {
      debugPrint('VoiceProvider.speakResponse: no ApiClient available');
      return;
    }

    try {
      final bytes = await client.synthesizeSpeech(text);
      if (bytes != null && bytes.isNotEmpty) {
        await _service.playTts(bytes);
      }
    } catch (e) {
      debugPrint('VoiceProvider.speakResponse error: $e');
    }
  }

  @override
  void dispose() {
    _service.removeListener(_onServiceChanged);
    _service.dispose();
    super.dispose();
  }
}
