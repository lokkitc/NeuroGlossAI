import '../../domain/entities/character.dart';
import '../../domain/repositories/characters_repository.dart';
import '../datasources/characters_remote_data_source.dart';
import '../dto/character_dto.dart';
import '../mappers/character_mapper.dart';

class CharactersRepositoryImpl implements CharactersRepository {
  CharactersRepositoryImpl(this._remote);

  final CharactersRemoteDataSource _remote;

  @override
  Future<List<CharacterEntity>> listMy({int skip = 0, int limit = 50}) async {
    final raw = await _remote.listMy(skip: skip, limit: limit);
    return raw.map((e) => CharacterMapper.toEntity(CharacterDto.fromJson(e))).toList(growable: false);
  }

  @override
  Future<CharacterEntity> create({
    required String slug,
    required String displayName,
    required String systemPrompt,
    String description = '',
    String? stylePrompt,
    bool isPublic = false,
    bool isNsfw = false,
    Map<String, dynamic>? settings,
  }) async {
    final json = await _remote.create({
      'slug': slug,
      'display_name': displayName,
      'description': description,
      'system_prompt': systemPrompt,
      'style_prompt': stylePrompt,
      'is_public': isPublic,
      'is_nsfw': isNsfw,
      'settings': settings,
    });
    return CharacterMapper.toEntity(CharacterDto.fromJson(json));
  }

  @override
  Future<void> delete(String id) => _remote.delete(id);
}
