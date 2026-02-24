class MemoryItemDto {
  const MemoryItemDto({
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

  factory MemoryItemDto.fromJson(Map<String, dynamic> json) {
    final rawTags = json['tags'];
    return MemoryItemDto(
      id: (json['id'] ?? '').toString(),
      ownerUserId: (json['owner_user_id'] ?? '').toString(),
      characterId: json['character_id']?.toString(),
      roomId: json['room_id']?.toString(),
      sessionId: json['session_id']?.toString(),
      title: (json['title'] ?? '').toString(),
      content: (json['content'] ?? '').toString(),
      isPinned: json['is_pinned'] == true,
      isEnabled: json['is_enabled'] != false,
      tags: rawTags is List ? rawTags.map((e) => e.toString()).toList(growable: false) : null,
      importance: (json['importance'] is num) ? (json['importance'] as num).toInt() : int.tryParse('${json['importance']}') ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'owner_user_id': ownerUserId,
        'character_id': characterId,
        'room_id': roomId,
        'session_id': sessionId,
        'title': title,
        'content': content,
        'is_pinned': isPinned,
        'is_enabled': isEnabled,
        'tags': tags,
        'importance': importance,
      };
}
