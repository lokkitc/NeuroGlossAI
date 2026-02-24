import 'package:json_annotation/json_annotation.dart';

part 'chat_turn_dto.g.dart';

@JsonSerializable(fieldRename: FieldRename.snake)
class ChatTurnDto {
  const ChatTurnDto({
    required this.id,
    required this.sessionId,
    required this.turnIndex,
    required this.role,
    required this.content,
    this.characterId,
    this.meta,
  });

  final String id;
  final String sessionId;
  final int turnIndex;
  final String role;
  final String content;
  final String? characterId;
  final Map<String, dynamic>? meta;

  factory ChatTurnDto.fromJson(Map<String, dynamic> json) => _$ChatTurnDtoFromJson(json);
  Map<String, dynamic> toJson() => _$ChatTurnDtoToJson(this);
}
