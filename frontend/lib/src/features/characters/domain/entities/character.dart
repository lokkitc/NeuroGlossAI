import 'package:equatable/equatable.dart';

class CharacterEntity extends Equatable {
  const CharacterEntity({
    required this.id,
    required this.ownerUserId,
    required this.slug,
    required this.displayName,
    required this.description,
    required this.systemPrompt,
    required this.stylePrompt,
    required this.avatarUrl,
    required this.thumbnailUrl,
    required this.bannerUrl,
    required this.greeting,
    required this.tags,
    required this.voiceProvider,
    required this.voiceId,
    required this.voiceSettings,
    required this.chatSettings,
    required this.isPublic,
    required this.isNsfw,
    required this.settings,
  });

  final String id;
  final String ownerUserId;
  final String slug;
  final String displayName;
  final String description;
  final String systemPrompt;
  final String? stylePrompt;
  final String? avatarUrl;
  final String? thumbnailUrl;
  final String? bannerUrl;
  final String? greeting;
  final List<String>? tags;
  final String? voiceProvider;
  final String? voiceId;
  final Map<String, dynamic>? voiceSettings;
  final Map<String, dynamic>? chatSettings;
  final bool isPublic;
  final bool isNsfw;
  final Map<String, dynamic>? settings;

  @override
  List<Object?> get props => [
        id,
        ownerUserId,
        slug,
        displayName,
        description,
        systemPrompt,
        stylePrompt,
        avatarUrl,
        thumbnailUrl,
        bannerUrl,
        greeting,
        tags,
        voiceProvider,
        voiceId,
        voiceSettings,
        chatSettings,
        isPublic,
        isNsfw,
        settings,
      ];
}
