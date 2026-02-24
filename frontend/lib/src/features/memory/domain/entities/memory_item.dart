import 'package:equatable/equatable.dart';

class MemoryItemEntity extends Equatable {
  const MemoryItemEntity({
    required this.id,
    required this.ownerUserId,
    required this.characterId,
    required this.roomId,
    required this.sessionId,
    required this.title,
    required this.content,
    required this.isPinned,
    required this.isEnabled,
    required this.tags,
    required this.importance,
  });

  final String id;
  final String ownerUserId;
  final String? characterId;
  final String? roomId;
  final String? sessionId;
  final String title;
  final String content;
  final bool isPinned;
  final bool isEnabled;
  final List<String>? tags;
  final int importance;

  @override
  List<Object?> get props => [
        id,
        ownerUserId,
        characterId,
        roomId,
        sessionId,
        title,
        content,
        isPinned,
        isEnabled,
        tags,
        importance,
      ];
}
