import 'package:equatable/equatable.dart';

class UserEntity extends Equatable {
  const UserEntity({
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

  final String? avatarUrl;
  final String? thumbnailUrl;
  final String? bannerUrl;
  final String? preferredName;
  final String? bio;
  final String? timezone;
  final String? uiTheme;
  final String? assistantTone;
  final int? assistantVerbosity;
  final Map<String, dynamic>? preferences;

  final String? targetLanguage;
  final String? nativeLanguage;
  final List<String>? interests;
  final int? xp;

  @override
  List<Object?> get props => [
        id,
        username,
        email,
        avatarUrl,
        thumbnailUrl,
        bannerUrl,
        preferredName,
        bio,
        timezone,
        uiTheme,
        assistantTone,
        assistantVerbosity,
        preferences,
        targetLanguage,
        nativeLanguage,
        interests,
        xp,
      ];
}
