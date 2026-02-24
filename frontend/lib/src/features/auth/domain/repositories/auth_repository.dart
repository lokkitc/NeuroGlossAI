import '../entities/auth_session.dart';
import '../entities/user.dart';

abstract class AuthRepository {
  Future<AuthSession> login({required String username, required String password});
  Future<UserEntity> me();
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
    String? assistantTone,
    int? assistantVerbosity,
    Map<String, dynamic>? preferences,
    String? targetLanguage,
    String? nativeLanguage,
    List<String>? interests,
  });
  Future<void> logout();

  Future<bool> hasToken();
}
