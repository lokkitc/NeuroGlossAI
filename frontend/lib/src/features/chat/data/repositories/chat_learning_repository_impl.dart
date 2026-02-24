import '../../domain/entities/chat_learning_lesson.dart';
import '../../domain/repositories/chat_learning_repository.dart';
import '../datasources/chat_learning_remote_data_source.dart';
import '../dto/chat_learning_lesson_dto.dart';
import '../mappers/chat_learning_mapper.dart';

class ChatLearningRepositoryImpl implements ChatLearningRepository {
  ChatLearningRepositoryImpl(this._remote);

  final ChatLearningRemoteDataSource _remote;

  @override
  Future<List<ChatLearningLessonEntity>> listLessons(String sessionId, {int skip = 0, int limit = 50}) async {
    final raw = await _remote.listLessons(sessionId, skip: skip, limit: limit);
    return raw.map((e) => ChatLearningMapper.toEntity(ChatLearningLessonDto.fromJson(e))).toList(growable: false);
  }

  @override
  Future<ChatLearningLessonEntity> generateLesson(String sessionId, {int turnWindow = 40, String generationMode = 'balanced'}) async {
    final json = await _remote.generateLesson(sessionId, turnWindow: turnWindow, generationMode: generationMode);
    return ChatLearningMapper.toEntity(ChatLearningLessonDto.fromJson(json));
  }
}
