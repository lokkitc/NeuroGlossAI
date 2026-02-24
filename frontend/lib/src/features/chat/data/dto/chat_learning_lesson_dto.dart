class ChatLearningLessonDto {
  const ChatLearningLessonDto({
    required this.id,
    required this.ownerUserId,
    required this.chatSessionId,
    required this.sourceTurnFrom,
    required this.sourceTurnTo,
    required this.title,
    required this.topicSnapshot,
    required this.contentText,
    required this.vocabulary,
    required this.exercises,
    required this.provider,
    required this.model,
    required this.qualityStatus,
    required this.createdAt,
  });

  final String id;
  final String ownerUserId;
  final String chatSessionId;
  final int sourceTurnFrom;
  final int sourceTurnTo;
  final String title;
  final String? topicSnapshot;
  final String contentText;
  final Object? vocabulary;
  final Object? exercises;
  final String? provider;
  final String? model;
  final String? qualityStatus;
  final DateTime? createdAt;

  factory ChatLearningLessonDto.fromJson(Map<String, dynamic> json) {
    DateTime? parsed;
    final raw = json['created_at'];
    if (raw is String) {
      parsed = DateTime.tryParse(raw);
    }

    int _asInt(dynamic v) {
      if (v is int) return v;
      if (v is num) return v.toInt();
      return int.tryParse('$v') ?? 0;
    }

    return ChatLearningLessonDto(
      id: (json['id'] ?? '').toString(),
      ownerUserId: (json['owner_user_id'] ?? '').toString(),
      chatSessionId: (json['chat_session_id'] ?? '').toString(),
      sourceTurnFrom: _asInt(json['source_turn_from']),
      sourceTurnTo: _asInt(json['source_turn_to']),
      title: (json['title'] ?? '').toString(),
      topicSnapshot: json['topic_snapshot']?.toString(),
      contentText: (json['content_text'] ?? '').toString(),
      vocabulary: json['vocabulary'],
      exercises: json['exercises'],
      provider: json['provider']?.toString(),
      model: json['model']?.toString(),
      qualityStatus: json['quality_status']?.toString(),
      createdAt: parsed,
    );
  }
}
