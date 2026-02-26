import '../../../../core/errors/app_exception.dart';
import '../../../../core/network/token_storage.dart';
import '../../domain/entities/auth_session.dart';
import '../../domain/entities/user.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_remote_data_source.dart';
import '../mappers/auth_mapper.dart';

class AuthRepositoryImpl implements AuthRepository {
  AuthRepositoryImpl(this._remote, this._tokenStorage);

  final AuthRemoteDataSource _remote;
  final TokenStorage _tokenStorage;

  @override
  Future<AuthSession> login({required String username, required String password}) async {
    final dto = await _remote.login(username: username, password: password);
    final entity = AuthMapper.toEntity(dto);
    await _tokenStorage.writeAccessToken(entity.accessToken);
    await _tokenStorage.writeRefreshToken(entity.refreshToken);
    await _tokenStorage.writeSessionId(entity.sessionId);
    return entity;
  }

  @override
  Future<UserEntity> me() async {
    final dto = await _remote.me();
    return AuthMapper.toEntityUser(dto);
  }

  @override
  Future<UserEntity> updateMe({
    String? username,
    String? email,
    String? avatarUrl,
    String? thumbnailUrl,
    String? bannerUrl,
    String? preferredName,
    String? bio,
    String? timezone,
    String? uiTheme,
    String? selectedThemeId,
    String? assistantTone,
    int? assistantVerbosity,
    Map<String, dynamic>? preferences,
    String? targetLanguage,
    String? nativeLanguage,
    List<String>? interests,
  }) async {
    final dto = await _remote.updateMe({
      if (username != null) 'username': username,
      if (email != null) 'email': email,
      if (avatarUrl != null) 'avatar_url': avatarUrl,
      if (thumbnailUrl != null) 'thumbnail_url': thumbnailUrl,
      if (bannerUrl != null) 'banner_url': bannerUrl,
      if (preferredName != null) 'preferred_name': preferredName,
      if (bio != null) 'bio': bio,
      if (timezone != null) 'timezone': timezone,
      if (uiTheme != null) 'ui_theme': uiTheme,
      if (selectedThemeId != null) 'selected_theme_id': selectedThemeId,
      if (assistantTone != null) 'assistant_tone': assistantTone,
      if (assistantVerbosity != null) 'assistant_verbosity': assistantVerbosity,
      if (preferences != null) 'preferences': preferences,
      if (targetLanguage != null) 'target_language': targetLanguage,
      if (nativeLanguage != null) 'native_language': nativeLanguage,
      if (interests != null) 'interests': interests,
    });
    return AuthMapper.toEntityUser(dto);
  }

  @override
  Future<void> logout() async {
    final rt = await _tokenStorage.readRefreshToken();
    if (rt != null && rt.isNotEmpty) {
      try {
        await _remote.logout(refreshToken: rt);
      } on AppException {
      } catch (_) {
      }
    }
    await _tokenStorage.clear();
  }

  @override
  Future<bool> hasToken() async {
    final t = await _tokenStorage.readAccessToken();
    return t != null && t.isNotEmpty;
  }

  Future<AuthSession> refresh() async {
    final rt = await _tokenStorage.readRefreshToken();
    if (rt == null || rt.isEmpty) {
      throw const UnauthorizedException('Unauthorized');
    }
    final dto = await _remote.refresh(refreshToken: rt);
    final entity = AuthMapper.toEntity(dto);
    await _tokenStorage.writeAccessToken(entity.accessToken);
    await _tokenStorage.writeRefreshToken(entity.refreshToken);
    await _tokenStorage.writeSessionId(entity.sessionId);
    return entity;
  }

  Future<UserEntity?> tryMe() async {
    try {
      return await me();
    } on UnauthorizedException {
      await logout();
      return null;
    }
  }
}
