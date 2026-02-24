import '../../domain/entities/chat_session.dart';
import '../../domain/entities/chat_session_detail.dart';
import '../../domain/entities/chat_turn.dart';
import '../dto/chat_session_dto.dart';
import '../dto/chat_session_detail_dto.dart';
import '../dto/chat_turn_dto.dart';
import '../dto/chat_turn_response_dto.dart';

class ChatMapper {
  static ChatSessionEntity session(ChatSessionDto dto) {
    return ChatSessionEntity(
      id: dto.id,
      ownerUserId: dto.ownerUserId,
      title: dto.title,
      isArchived: dto.isArchived,
      characterId: dto.characterId,
      roomId: dto.roomId,
      enrollmentId: dto.enrollmentId,
      activeLevelTemplateId: dto.activeLevelTemplateId,
    );
  }

  static ChatTurnEntity turn(ChatTurnDto dto) {
    return ChatTurnEntity(
      id: dto.id,
      sessionId: dto.sessionId,
      turnIndex: dto.turnIndex,
      role: dto.role,
      characterId: dto.characterId,
      content: dto.content,
      meta: dto.meta,
    );
  }

  static ChatSessionDetailEntity detail(ChatSessionDetailDto dto) {
    return ChatSessionDetailEntity(
      session: session(dto),
      turns: dto.turns.map(turn).toList(growable: false),
    );
  }

  static ChatSessionDetailEntity afterTurn(ChatTurnResponseDto dto, {List<ChatTurnDto>? priorTurns}) {
    final turns = <ChatTurnDto>[];
    if (priorTurns != null) turns.addAll(priorTurns);
    turns.add(dto.userTurn);
    turns.addAll(dto.assistantTurns);
    return ChatSessionDetailEntity(
      session: session(dto.session),
      turns: turns.map(turn).toList(growable: false),
    );
  }
}
