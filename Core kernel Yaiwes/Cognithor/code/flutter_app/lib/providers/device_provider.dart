/// Provides device sensor data (location, battery, network) to Cognithor.
/// User can control which data is shared.
library;

import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:battery_plus/battery_plus.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:permission_handler/permission_handler.dart';

/// Provides device-level context (location, battery, network, camera, mic)
/// that can be attached to Cognithor messages.
class DeviceProvider extends ChangeNotifier {
  // ---------------------------------------------------------------------------
  // Permission toggles (user-controlled)
  // ---------------------------------------------------------------------------
  bool locationEnabled = false;
  bool cameraEnabled = false;
  bool microphoneEnabled = false;
  bool photosEnabled = false;

  // ---------------------------------------------------------------------------
  // Current data
  // ---------------------------------------------------------------------------
  Position? lastPosition;
  int? batteryLevel;
  String? networkType; // wifi, mobile, none
  Map<String, dynamic>? deviceInfo;

  // ---------------------------------------------------------------------------
  // Internals
  // ---------------------------------------------------------------------------
  final Battery _battery = Battery();
  final Connectivity _connectivity = Connectivity();
  final DeviceInfoPlugin _deviceInfoPlugin = DeviceInfoPlugin();
  final ImagePicker _imagePicker = ImagePicker();

  // ---------------------------------------------------------------------------
  // Permissions
  // ---------------------------------------------------------------------------

  /// Request all permissions the user has enabled.
  Future<void> requestPermissions() async {
    if (kIsWeb) return; // Permissions are browser-managed on web.

    final statuses = await [
      Permission.location,
      Permission.camera,
      Permission.microphone,
      Permission.photos,
    ].request();

    locationEnabled = statuses[Permission.location]?.isGranted ?? false;
    cameraEnabled = statuses[Permission.camera]?.isGranted ?? false;
    microphoneEnabled = statuses[Permission.microphone]?.isGranted ?? false;
    photosEnabled = statuses[Permission.photos]?.isGranted ?? false;

    notifyListeners();
  }

  /// Request a single permission and update the corresponding toggle.
  Future<bool> requestSinglePermission(Permission permission) async {
    if (kIsWeb) return false;

    final status = await permission.request();
    final granted = status.isGranted;

    switch (permission) {
      case Permission.location:
        locationEnabled = granted;
      case Permission.camera:
        cameraEnabled = granted;
      case Permission.microphone:
        microphoneEnabled = granted;
      case Permission.photos:
        photosEnabled = granted;
      default:
        break;
    }
    notifyListeners();
    return granted;
  }

  /// Enable sharing for a specific permission (web: app-level toggle only).
  void enablePermission(Permission permission) {
    switch (permission) {
      case Permission.location:
        locationEnabled = true;
      case Permission.camera:
        cameraEnabled = true;
      case Permission.microphone:
        microphoneEnabled = true;
      case Permission.photos:
        photosEnabled = true;
      default:
        break;
    }
    notifyListeners();
  }

  /// Disable sharing for a specific permission (user opt-out).
  void disablePermission(Permission permission) {
    switch (permission) {
      case Permission.location:
        locationEnabled = false;
      case Permission.camera:
        cameraEnabled = false;
      case Permission.microphone:
        microphoneEnabled = false;
      case Permission.photos:
        photosEnabled = false;
      default:
        break;
    }
    notifyListeners();
  }

  // ---------------------------------------------------------------------------
  // Location
  // ---------------------------------------------------------------------------

  /// Get current location (returns null when permission denied or unavailable).
  Future<Position?> getCurrentLocation() async {
    if (kIsWeb || !locationEnabled) return null;

    try {
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) return null;

      lastPosition = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 10),
        ),
      );
      notifyListeners();
      return lastPosition;
    } catch (_) {
      return null;
    }
  }

  // ---------------------------------------------------------------------------
  // Battery
  // ---------------------------------------------------------------------------

  Future<int?> getBatteryLevel() async {
    if (kIsWeb) return null;
    try {
      batteryLevel = await _battery.batteryLevel;
      notifyListeners();
      return batteryLevel;
    } catch (_) {
      return null;
    }
  }

  // ---------------------------------------------------------------------------
  // Network
  // ---------------------------------------------------------------------------

  Future<String?> getNetworkType() async {
    try {
      final result = await _connectivity.checkConnectivity();
      if (result.contains(ConnectivityResult.wifi)) {
        networkType = 'wifi';
      } else if (result.contains(ConnectivityResult.mobile)) {
        networkType = 'mobile';
      } else if (result.contains(ConnectivityResult.ethernet)) {
        networkType = 'ethernet';
      } else {
        networkType = 'none';
      }
      notifyListeners();
      return networkType;
    } catch (_) {
      return null;
    }
  }

  // ---------------------------------------------------------------------------
  // Device info
  // ---------------------------------------------------------------------------

  Future<Map<String, dynamic>?> getDeviceInfo() async {
    if (kIsWeb) return null;
    try {
      final info = await _deviceInfoPlugin.deviceInfo;
      deviceInfo = info.data;
      notifyListeners();
      return deviceInfo;
    } catch (_) {
      return null;
    }
  }

  // ---------------------------------------------------------------------------
  // Device context (sent with messages)
  // ---------------------------------------------------------------------------

  /// Collects all available device context into a map suitable for attaching
  /// to Cognithor chat messages.
  Map<String, dynamic> getDeviceContext() {
    return {
      if (locationEnabled && lastPosition != null)
        'location': {
          'lat': lastPosition!.latitude,
          'lon': lastPosition!.longitude,
          'accuracy': lastPosition!.accuracy,
        },
      if (batteryLevel != null) 'battery': batteryLevel,
      if (networkType != null) 'network': networkType,
      if (deviceInfo != null) 'device': deviceInfo,
    };
  }

  // ---------------------------------------------------------------------------
  // Camera / Photos
  // ---------------------------------------------------------------------------

  /// Take a photo and return its bytes as a base64-encoded string.
  Future<String?> capturePhoto() async {
    if (kIsWeb || !cameraEnabled) return null;
    try {
      final XFile? photo = await _imagePicker.pickImage(
        source: ImageSource.camera,
        maxWidth: 1920,
        maxHeight: 1080,
        imageQuality: 85,
      );
      if (photo == null) return null;
      final Uint8List bytes = await photo.readAsBytes();
      return base64Encode(bytes);
    } catch (_) {
      return null;
    }
  }

  /// Pick an image from the gallery and return base64.
  Future<String?> pickPhoto() async {
    if (kIsWeb || !photosEnabled) return null;
    try {
      final XFile? photo = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1920,
        maxHeight: 1080,
        imageQuality: 85,
      );
      if (photo == null) return null;
      final Uint8List bytes = await photo.readAsBytes();
      return base64Encode(bytes);
    } catch (_) {
      return null;
    }
  }

  // ---------------------------------------------------------------------------
  // Audio recording (stub — record package requires platform-specific setup)
  // ---------------------------------------------------------------------------

  /// Record audio and return base64. Duration limited to [maxDuration].
  ///
  /// Note: Full implementation requires the `record` package to be wired with
  /// platform-specific configuration. This stub returns null on unsupported
  /// platforms and on web.
  Future<String?> recordAudio({
    Duration maxDuration = const Duration(seconds: 30),
  }) async {
    // TODO: Wire up the `record` package for real audio capture.
    // For now, return null to avoid crashes on platforms without mic setup.
    return null;
  }

  // ---------------------------------------------------------------------------
  // Refresh all sensors
  // ---------------------------------------------------------------------------

  /// Refresh all sensor data in one go.
  Future<void> refreshAll() async {
    await Future.wait([
      getCurrentLocation(),
      getBatteryLevel(),
      getNetworkType(),
      getDeviceInfo(),
    ]);
  }
}
