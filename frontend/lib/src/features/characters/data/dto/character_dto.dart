import 'package:json_annotation/json_annotation.dart';

part 'character_dto.g.dart';

@JsonSerializable(fieldRename: FieldRename.snake)
class CharacterDto {
  const CharacterDto({
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
    required this.chatThemeId,
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
  final String? chatThemeId;
  final bool isPublic;
  final bool isNsfw;
  final Map<String, dynamic>? settings;

  factory CharacterDto.fromJson(Map<String, dynamic> json) => _$CharacterDtoFromJson(json);
  Map<String, dynamic> toJson() => _$CharacterDtoToJson(this);
}
