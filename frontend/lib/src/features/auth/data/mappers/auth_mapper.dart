import '../../domain/entities/auth_session.dart';
import '../../domain/entities/user.dart';
import '../dto/auth_session_dto.dart';
import '../dto/user_dto.dart';

class AuthMapper {
  static AuthSession toEntity(AuthSessionDto dto) {
    return AuthSession(accessToken: dto.accessToken, refreshToken: dto.refreshToken, sessionId: dto.sessionId);
  }

  static UserEntity toEntityUser(UserDto dto) {
    return UserEntity(
      id: dto.id,
      username: dto.username,
      email: dto.email,
      avatarUrl: dto.avatarUrl,
      thumbnailUrl: dto.thumbnailUrl,
      bannerUrl: dto.bannerUrl,
      preferredName: dto.preferredName,
      bio: dto.bio,
      timezone: dto.timezone,
      uiTheme: dto.uiTheme,
      selectedThemeId: dto.selectedThemeId,
      assistantTone: dto.assistantTone,
      assistantVerbosity: dto.assistantVerbosity,
      preferences: dto.preferences,
      targetLanguage: dto.targetLanguage,
      nativeLanguage: dto.nativeLanguage,
      interests: dto.interests,
      xp: dto.xp,
    );
  }
}
