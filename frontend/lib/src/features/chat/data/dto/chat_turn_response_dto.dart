import 'package:json_annotation/json_annotation.dart';

import 'chat_session_dto.dart';
import 'chat_turn_dto.dart';

part 'chat_turn_response_dto.g.dart';

@JsonSerializable(fieldRename: FieldRename.snake)
class ChatTurnResponseDto {
  const ChatTurnResponseDto({
    required this.session,
    required this.userTurn,
    required this.assistantTurns,
    required this.memoryUsed,
  });

  final ChatSessionDto session;
  final ChatTurnDto userTurn;
  final List<ChatTurnDto> assistantTurns;
  final List<dynamic> memoryUsed;

  factory ChatTurnResponseDto.fromJson(Map<String, dynamic> json) => _$ChatTurnResponseDtoFromJson(json);
  Map<String, dynamic> toJson() => _$ChatTurnResponseDtoToJson(this);
}
