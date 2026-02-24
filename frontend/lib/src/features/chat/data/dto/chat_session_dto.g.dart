// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'chat_session_dto.dart';

// ***************************************************************************
// JsonSerializableGenerator
// ***************************************************************************

ChatSessionDto _$ChatSessionDtoFromJson(Map<String, dynamic> json) => ChatSessionDto(
      id: json['id'] as String,
      ownerUserId: json['owner_user_id'] as String,
      title: json['title'] as String,
      isArchived: json['is_archived'] as bool,
      characterId: json['character_id'] as String?,
      roomId: json['room_id'] as String?,
      enrollmentId: json['enrollment_id'] as String?,
      activeLevelTemplateId: json['active_level_template_id'] as String?,
    );

Map<String, dynamic> _$ChatSessionDtoToJson(ChatSessionDto instance) => <String, dynamic>{
      'id': instance.id,
      'owner_user_id': instance.ownerUserId,
      'character_id': instance.characterId,
      'room_id': instance.roomId,
      'enrollment_id': instance.enrollmentId,
      'active_level_template_id': instance.activeLevelTemplateId,
      'title': instance.title,
      'is_archived': instance.isArchived,
    };
