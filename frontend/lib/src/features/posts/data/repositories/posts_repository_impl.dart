import '../../domain/entities/post.dart';
import '../../domain/repositories/posts_repository.dart';
import '../datasources/posts_remote_data_source.dart';
import '../mappers/post_mapper.dart';

class PostsRepositoryImpl implements PostsRepository {
  PostsRepositoryImpl(this._remote);

  final PostsRemoteDataSource _remote;

  @override
  Future<List<PostEntity>> listPublic({int skip = 0, int limit = 50}) async {
    final raw = await _remote.listPublic(skip: skip, limit: limit);
    return raw.map(PostMapper.fromJson).toList(growable: false);
  }

  @override
  Future<List<PostEntity>> listPublicByUsername({required String username, int skip = 0, int limit = 50}) async {
    final raw = await _remote.listPublicByUsername(username: username, skip: skip, limit: limit);
    return raw.map(PostMapper.fromJson).toList(growable: false);
  }

  @override
  Future<List<PostEntity>> listPublicByCharacter({required String characterId, int skip = 0, int limit = 50}) async {
    final raw = await _remote.listPublicByCharacter(characterId: characterId, skip: skip, limit: limit);
    return raw.map(PostMapper.fromJson).toList(growable: false);
  }

  @override
  Future<List<PostEntity>> listMine({int skip = 0, int limit = 50}) async {
    final raw = await _remote.listMine(skip: skip, limit: limit);
    return raw.map(PostMapper.fromJson).toList(growable: false);
  }

  @override
  Future<PostEntity> create({
    String title = '',
    String content = '',
    bool isPublic = true,
    String? characterId,
    List<PostMediaEntity>? media,
  }) async {
    final payload = <String, dynamic>{
      'title': title,
      'content': content,
      'is_public': isPublic,
      'character_id': characterId,
      'media': media?.map(PostMapper.mediaToJson).toList(growable: false),
    };
    final json = await _remote.create(payload);
    return PostMapper.fromJson(json);
  }

  @override
  Future<PostEntity> setPublic({required String id, required bool isPublic}) async {
    final json = await _remote.share(id: id, isPublic: isPublic);
    return PostMapper.fromJson(json);
  }

  @override
  Future<void> delete(String id) => _remote.delete(id);

  @override
  Future<void> like(String id) => _remote.like(id);

  @override
  Future<void> unlike(String id) => _remote.unlike(id);
}
