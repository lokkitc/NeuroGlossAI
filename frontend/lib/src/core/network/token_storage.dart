import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'dart:math';

class TokenStorage {
  TokenStorage(this._storage);

  final FlutterSecureStorage _storage;

  static const _kAccessTokenKey = 'access_token';
  static const _kRefreshTokenKey = 'refresh_token';
  static const _kSessionIdKey = 'session_id';
  static const _kDeviceIdKey = 'device_id';

  Future<String?> readAccessToken() => _storage.read(key: _kAccessTokenKey);

  Future<void> writeAccessToken(String token) => _storage.write(key: _kAccessTokenKey, value: token);

  Future<String?> readRefreshToken() => _storage.read(key: _kRefreshTokenKey);

  Future<void> writeRefreshToken(String token) => _storage.write(key: _kRefreshTokenKey, value: token);

  Future<String?> readSessionId() => _storage.read(key: _kSessionIdKey);

  Future<void> writeSessionId(String sessionId) => _storage.write(key: _kSessionIdKey, value: sessionId);

  Future<String?> readDeviceId() => _storage.read(key: _kDeviceIdKey);

  Future<void> writeDeviceId(String deviceId) => _storage.write(key: _kDeviceIdKey, value: deviceId);

  Future<String> ensureDeviceId() async {
    final existing = await readDeviceId();
    if (existing != null && existing.isNotEmpty) return existing;
    final now = DateTime.now().microsecondsSinceEpoch;
    final rand = Random.secure().nextInt(1 << 31);
    final id = '$now-$rand';
    await writeDeviceId(id);
    return id;
  }

  Future<void> clear() async {
    await _storage.delete(key: _kAccessTokenKey);
    await _storage.delete(key: _kRefreshTokenKey);
    await _storage.delete(key: _kSessionIdKey);
  }
}
