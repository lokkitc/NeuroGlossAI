import '../../domain/entities/memory_item.dart';
import '../dto/memory_item_dto.dart';

class MemoryMapper {
  static MemoryItemEntity toEntity(MemoryItemDto dto) {
    return MemoryItemEntity(
      id: dto.id,
      ownerUserId: dto.ownerUserId,
      characterId: dto.characterId,
      roomId: dto.roomId,
      sessionId: dto.sessionId,
      title: dto.title,
      content: dto.content,
      isPinned: dto.isPinned,
      isEnabled: dto.isEnabled,
      tags: dto.tags,
      importance: dto.importance,
    );
  }
}
