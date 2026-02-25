import '../entities/chat_learning_lesson.dart';

abstract class ChatLearningRepository {
  Future<List<ChatLearningLessonEntity>> listLessons(String sessionId, {int skip = 0, int limit = 50});

  Future<ChatLearningLessonEntity> generateLesson(
    String sessionId, {
    int turnWindow = 80,
    String generationMode = 'balanced',
  });
}
