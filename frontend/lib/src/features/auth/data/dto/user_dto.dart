import 'package:json_annotation/json_annotation.dart';

part 'user_dto.g.dart';

@JsonSerializable()
class UserDto {
  const UserDto({
    required this.id,
    required this.username,
    required this.email,
    this.avatarUrl,
    this.thumbnailUrl,
    this.bannerUrl,
    this.preferredName,
    this.bio,
    this.timezone,
    this.uiTheme,
    this.assistantTone,
    this.assistantVerbosity,
    this.preferences,
    this.targetLanguage,
    this.nativeLanguage,
    this.interests,
    this.xp,
  });

  final String id;
  final String username;
  final String email;

  @JsonKey(name: 'avatar_url')
  final String? avatarUrl;
  @JsonKey(name: 'thumbnail_url')
  final String? thumbnailUrl;
  @JsonKey(name: 'banner_url')
  final String? bannerUrl;
  @JsonKey(name: 'preferred_name')
  final String? preferredName;
  final String? bio;
  final String? timezone;
  @JsonKey(name: 'ui_theme')
  final String? uiTheme;
  @JsonKey(name: 'assistant_tone')
  final String? assistantTone;
  @JsonKey(name: 'assistant_verbosity')
  final int? assistantVerbosity;
  final Map<String, dynamic>? preferences;
  @JsonKey(name: 'target_language')
  final String? targetLanguage;
  @JsonKey(name: 'native_language')
  final String? nativeLanguage;
  final List<String>? interests;
  final int? xp;

  factory UserDto.fromJson(Map<String, dynamic> json) => _$UserDtoFromJson(json);
  Map<String, dynamic> toJson() => _$UserDtoToJson(this);
}
