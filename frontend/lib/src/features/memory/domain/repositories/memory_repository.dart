import '../entities/memory_item.dart';

abstract class MemoryRepository {
  Future<List<MemoryItemEntity>> listMy({int skip = 0, int limit = 100});

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
  });

  Future<MemoryItemEntity> update(
    String id, {
    String? title,
    String? content,
    bool? isPinned,
    bool? isEnabled,
    List<String>? tags,
    int? importance,
  });

  Future<void> delete(String id);
}
