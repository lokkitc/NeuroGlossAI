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
      isPublic: dto.isPublic,
      isNsfw: dto.isNsfw,
      settings: dto.settings,
    );
  }
}
