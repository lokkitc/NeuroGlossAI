import '../../domain/entities/chat_learning_lesson.dart';
import '../dto/chat_learning_lesson_dto.dart';

class ChatLearningMapper {
  static ChatLearningLessonEntity toEntity(ChatLearningLessonDto dto) {
    return ChatLearningLessonEntity(
      id: dto.id,
      ownerUserId: dto.ownerUserId,
      chatSessionId: dto.chatSessionId,
      sourceTurnFrom: dto.sourceTurnFrom,
      sourceTurnTo: dto.sourceTurnTo,
      title: dto.title,
      topicSnapshot: dto.topicSnapshot,
      contentText: dto.contentText,
      vocabulary: dto.vocabulary,
      exercises: dto.exercises,
      provider: dto.provider,
      model: dto.model,
      qualityStatus: dto.qualityStatus,
      createdAt: dto.createdAt,
    );
  }
}
