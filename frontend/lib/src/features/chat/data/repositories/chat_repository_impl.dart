import '../../domain/entities/chat_session.dart';
import '../../domain/entities/chat_session_detail.dart';
import '../../domain/repositories/chat_repository.dart';
import '../datasources/chat_remote_data_source.dart';
import '../dto/chat_session_dto.dart';
import '../dto/chat_session_detail_dto.dart';
import '../dto/chat_turn_response_dto.dart';
import '../mappers/chat_mapper.dart';

class ChatRepositoryImpl implements ChatRepository {
  ChatRepositoryImpl(this._remote);

  final ChatRemoteDataSource _remote;

  @override
  Future<List<ChatSessionEntity>> listSessions({int skip = 0, int limit = 50}) async {
    final raw = await _remote.listSessions(skip: skip, limit: limit);
    return raw.map((e) => ChatMapper.session(ChatSessionDto.fromJson(e))).toList(growable: false);
  }

  @override
  Future<ChatSessionEntity> createSession({String title = '', String? characterId, String? roomId}) async {
    final json = await _remote.createSession({'title': title, 'character_id': characterId, 'room_id': roomId});
    return ChatMapper.session(ChatSessionDto.fromJson(json));
  }

  @override
  Future<ChatSessionDetailEntity> getSession(String sessionId) async {
    final json = await _remote.getSession(sessionId);
    return ChatMapper.detail(ChatSessionDetailDto.fromJson(json));
  }

  @override
  Future<ChatSessionDetailEntity> sendTurn({required String sessionId, required String content}) async {
    final json = await _remote.sendTurn(sessionId, content);
    final dto = ChatTurnResponseDto.fromJson(json);
    // We will merge turns on controller level, so here return only incremental.
    return ChatMapper.afterTurn(dto);
  }
}
