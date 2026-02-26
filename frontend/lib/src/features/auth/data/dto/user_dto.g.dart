// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'user_dto.dart';

// ***************************************************************************
// JsonSerializableGenerator
// ***************************************************************************

UserDto _$UserDtoFromJson(Map<String, dynamic> json) => UserDto(
      id: json['id'] as String,
      username: json['username'] as String,
      email: json['email'] as String,
      avatarUrl: json['avatar_url'] as String?,
      thumbnailUrl: json['thumbnail_url'] as String?,
      bannerUrl: json['banner_url'] as String?,
      preferredName: json['preferred_name'] as String?,
      bio: json['bio'] as String?,
      timezone: json['timezone'] as String?,
      uiTheme: json['ui_theme'] as String?,
      selectedThemeId: json['selected_theme_id'] as String?,
      assistantTone: json['assistant_tone'] as String?,
      assistantVerbosity: (json['assistant_verbosity'] as num?)?.toInt(),
      preferences: json['preferences'] as Map<String, dynamic>?,
      targetLanguage: json['target_language'] as String?,
      nativeLanguage: json['native_language'] as String?,
      interests: (json['interests'] as List<dynamic>?)?.map((e) => e as String).toList(),
      xp: (json['xp'] as num?)?.toInt(),
    );

Map<String, dynamic> _$UserDtoToJson(UserDto instance) => <String, dynamic>{
      'id': instance.id,
      'username': instance.username,
      'email': instance.email,
      'avatar_url': instance.avatarUrl,
      'thumbnail_url': instance.thumbnailUrl,
      'banner_url': instance.bannerUrl,
      'preferred_name': instance.preferredName,
      'bio': instance.bio,
      'timezone': instance.timezone,
      'ui_theme': instance.uiTheme,
      'selected_theme_id': instance.selectedThemeId,
      'assistant_tone': instance.assistantTone,
      'assistant_verbosity': instance.assistantVerbosity,
      'preferences': instance.preferences,
      'target_language': instance.targetLanguage,
      'native_language': instance.nativeLanguage,
      'interests': instance.interests,
      'xp': instance.xp,
    };
