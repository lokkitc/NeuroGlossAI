// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'chat_turn_response_dto.dart';

// ***************************************************************************
// JsonSerializableGenerator
// ***************************************************************************

ChatTurnResponseDto _$ChatTurnResponseDtoFromJson(Map<String, dynamic> json) => ChatTurnResponseDto(
      session: ChatSessionDto.fromJson(Map<String, dynamic>.from(json['session'] as Map)),
      userTurn: ChatTurnDto.fromJson(Map<String, dynamic>.from(json['user_turn'] as Map)),
      assistantTurns: (json['assistant_turns'] as List<dynamic>? ?? const [])
          .map((e) => ChatTurnDto.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList(growable: false),
      memoryUsed: (json['memory_used'] as List<dynamic>? ?? const []),
    );

Map<String, dynamic> _$ChatTurnResponseDtoToJson(ChatTurnResponseDto instance) => <String, dynamic>{
      'session': instance.session.toJson(),
      'user_turn': instance.userTurn.toJson(),
      'assistant_turns': instance.assistantTurns.map((e) => e.toJson()).toList(growable: false),
      'memory_used': instance.memoryUsed,
    };
