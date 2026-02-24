import 'package:json_annotation/json_annotation.dart';

part 'chat_session_dto.g.dart';

@JsonSerializable(fieldRename: FieldRename.snake)
class ChatSessionDto {
  const ChatSessionDto({
    required this.id,
    required this.ownerUserId,
    required this.title,
    required this.isArchived,
    this.characterId,
    this.roomId,
    this.enrollmentId,
    this.activeLevelTemplateId,
  });

  final String id;
  final String ownerUserId;
  final String? characterId;
  final String? roomId;
  final String? enrollmentId;
  final String? activeLevelTemplateId;
  final String title;
  final bool isArchived;

  factory ChatSessionDto.fromJson(Map<String, dynamic> json) => _$ChatSessionDtoFromJson(json);
  Map<String, dynamic> toJson() => _$ChatSessionDtoToJson(this);
}
