// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'chat_turn_dto.dart';

// ***************************************************************************
// JsonSerializableGenerator
// ***************************************************************************

ChatTurnDto _$ChatTurnDtoFromJson(Map<String, dynamic> json) => ChatTurnDto(
      id: json['id'] as String,
      sessionId: json['session_id'] as String,
      turnIndex: (json['turn_index'] as num).toInt(),
      role: json['role'] as String,
      content: json['content'] as String,
      characterId: json['character_id'] as String?,
      meta: json['meta'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$ChatTurnDtoToJson(ChatTurnDto instance) => <String, dynamic>{
      'id': instance.id,
      'session_id': instance.sessionId,
      'turn_index': instance.turnIndex,
      'role': instance.role,
      'character_id': instance.characterId,
      'content': instance.content,
      'meta': instance.meta,
    };
