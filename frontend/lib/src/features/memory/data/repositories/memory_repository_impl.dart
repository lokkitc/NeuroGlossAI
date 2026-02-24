import '../../domain/entities/memory_item.dart';
import '../../domain/repositories/memory_repository.dart';
import '../datasources/memory_remote_data_source.dart';
import '../dto/memory_item_dto.dart';
import '../mappers/memory_mapper.dart';

class MemoryRepositoryImpl implements MemoryRepository {
  MemoryRepositoryImpl(this._remote);

  final MemoryRemoteDataSource _remote;

  @override
  Future<List<MemoryItemEntity>> listMy({int skip = 0, int limit = 100}) async {
    final raw = await _remote.listMy(skip: skip, limit: limit);
    return raw.map((e) => MemoryMapper.toEntity(MemoryItemDto.fromJson(e))).toList(growable: false);
  }

  @override
  Future<MemoryItemEntity> create({
    String title = '',
    required String content,
    String? characterId,
    String? roomId,
    String? sessionId,
    bool isPinned = false,
    bool isEnabled = true,
    List<String>? tags,
    int importance = 0,
  }) async {
    final json = await _remote.create({
      'title': title,
      'content': content,
      'character_id': characterId,
      'room_id': roomId,
      'session_id': sessionId,
      'is_pinned': isPinned,
      'is_enabled': isEnabled,
      'tags': tags,
      'importance': importance,
    });
    return MemoryMapper.toEntity(MemoryItemDto.fromJson(json));
  }

  @override
  Future<MemoryItemEntity> update(
    String id, {
    String? title,
    String? content,
    bool? isPinned,
    bool? isEnabled,
    List<String>? tags,
    int? importance,
  }) async {
    final json = await _remote.update(id, {
      if (title != null) 'title': title,
      if (content != null) 'content': content,
      if (isPinned != null) 'is_pinned': isPinned,
      if (isEnabled != null) 'is_enabled': isEnabled,
      if (tags != null) 'tags': tags,
      if (importance != null) 'importance': importance,
    });
    return MemoryMapper.toEntity(MemoryItemDto.fromJson(json));
  }

  @override
  Future<void> delete(String id) => _remote.delete(id);
}
