import '../../domain/entities/character.dart';
import '../dto/character_dto.dart';

class CharacterMapper {
  static CharacterEntity toEntity(CharacterDto dto) {
    return CharacterEntity(
      id: dto.id,
      ownerUserId: dto.ownerUserId,
      slug: dto.slug,
      displayName: dto.displayName,
      description: dto.description,
      systemPrompt: dto.systemPrompt,
      stylePrompt: dto.stylePrompt,
      avatarUrl: dto.avatarUrl,
      thumbnailUrl: dto.thumbnailUrl,
      bannerUrl: dto.bannerUrl,
      greeting: dto.greeting,
      tags: dto.tags,
      voiceProvider: dto.voiceProvider,
      voiceId: dto.voiceId,
      voiceSettings: dto.voiceSettings,
      chatSettings: dto.chatSettings,
      isPublic: dto.isPublic,
      isNsfw: dto.isNsfw,
      settings: dto.settings,
    );
  }
}
