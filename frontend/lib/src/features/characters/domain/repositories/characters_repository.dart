import '../entities/character.dart';

abstract class CharactersRepository {
  Future<List<CharacterEntity>> listMy({int skip = 0, int limit = 50});
  Future<CharacterEntity> create({
    required String slug,
    required String displayName,
    required String systemPrompt,
    String description = '',
    String? stylePrompt,
    bool isPublic = false,
    bool isNsfw = false,
    Map<String, dynamic>? settings,
  });

  Future<void> delete(String id);
}
