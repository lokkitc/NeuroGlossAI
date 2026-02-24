import 'package:json_annotation/json_annotation.dart';

import 'chat_session_dto.dart';
import 'chat_turn_dto.dart';

part 'chat_session_detail_dto.g.dart';

@JsonSerializable(fieldRename: FieldRename.snake)
class ChatSessionDetailDto extends ChatSessionDto {
  const ChatSessionDetailDto({
    required super.id,
    required super.ownerUserId,
    required super.title,
    required super.isArchived,
    super.characterId,
    super.roomId,
    super.enrollmentId,
    super.activeLevelTemplateId,
    required this.turns,
  });

  final List<ChatTurnDto> turns;

  factory ChatSessionDetailDto.fromJson(Map<String, dynamic> json) => _$ChatSessionDetailDtoFromJson(json);
  @override
  Map<String, dynamic> toJson() => _$ChatSessionDetailDtoToJson(this);
}
