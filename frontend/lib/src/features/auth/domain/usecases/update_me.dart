import '../entities/user.dart';
import '../repositories/auth_repository.dart';

class UpdateMeUseCase {
  const UpdateMeUseCase(this._repo);
  final AuthRepository _repo;

  Future<UserEntity> call({
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
  }) {
    return _repo.updateMe(
      username: username,
      email: email,
      avatarUrl: avatarUrl,
      thumbnailUrl: thumbnailUrl,
      bannerUrl: bannerUrl,
      preferredName: preferredName,
      bio: bio,
      timezone: timezone,
      uiTheme: uiTheme,
      assistantTone: assistantTone,
      assistantVerbosity: assistantVerbosity,
      preferences: preferences,
      targetLanguage: targetLanguage,
      nativeLanguage: nativeLanguage,
      interests: interests,
    );
  }
}
