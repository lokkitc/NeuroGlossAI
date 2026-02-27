import '../../domain/entities/public_user.dart';

class PublicUserMapper {
  static PublicUserEntity fromJson(Map<String, dynamic> json) {
    return PublicUserEntity(
      id: (json['id'] as String).trim(),
      username: (json['username'] as String).trim(),
      preferredName: (json['preferred_name'] as String?)?.trim(),
      bio: (json['bio'] as String?)?.trim(),
      selectedThemeId: (json['selected_theme_id'] as String?)?.trim(),
      avatarUrl: (json['avatar_url'] as String?)?.trim(),
      thumbnailUrl: (json['thumbnail_url'] as String?)?.trim(),
      bannerUrl: (json['banner_url'] as String?)?.trim(),
    );
  }
}
