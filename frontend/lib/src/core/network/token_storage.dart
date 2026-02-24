import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenStorage {
  TokenStorage(this._storage);

  final FlutterSecureStorage _storage;

  static const _kAccessTokenKey = 'access_token';

  Future<String?> readAccessToken() => _storage.read(key: _kAccessTokenKey);

  Future<void> writeAccessToken(String token) => _storage.write(key: _kAccessTokenKey, value: token);

  Future<void> clear() async {
    await _storage.delete(key: _kAccessTokenKey);
  }
}
