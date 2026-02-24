import '../entities/chat_session.dart';
import '../entities/chat_session_detail.dart';

abstract class ChatRepository {
  Future<List<ChatSessionEntity>> listSessions({int skip = 0, int limit = 50});
  Future<ChatSessionEntity> createSession({String title = '', String? characterId, String? roomId});
  Future<ChatSessionDetailEntity> getSession(String sessionId);

  Future<ChatSessionDetailEntity> sendTurn({required String sessionId, required String content});
}
