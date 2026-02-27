import '../entities/post.dart';

abstract class PostsRepository {
  Future<List<PostEntity>> listPublic({int skip = 0, int limit = 50});
  Future<List<PostEntity>> listPublicByUsername({required String username, int skip = 0, int limit = 50});
  Future<List<PostEntity>> listPublicByCharacter({required String characterId, int skip = 0, int limit = 50});
  Future<List<PostEntity>> listMine({int skip = 0, int limit = 50});
  Future<PostEntity> create({
    String title = '',
    String content = '',
    bool isPublic = true,
    String? characterId,
    List<PostMediaEntity>? media,
  });
  Future<PostEntity> setPublic({required String id, required bool isPublic});
  Future<void> delete(String id);
  Future<void> like(String id);
  Future<void> unlike(String id);
}
