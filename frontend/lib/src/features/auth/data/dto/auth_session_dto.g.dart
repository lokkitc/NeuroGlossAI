// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'auth_session_dto.dart';

// ***************************************************************************
// JsonSerializableGenerator
// ***************************************************************************

AuthSessionDto _$AuthSessionDtoFromJson(Map<String, dynamic> json) => AuthSessionDto(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      tokenType: json['token_type'] as String,
      sessionId: json['session_id'] as String,
    );

Map<String, dynamic> _$AuthSessionDtoToJson(AuthSessionDto instance) => <String, dynamic>{
      'access_token': instance.accessToken,
      'refresh_token': instance.refreshToken,
      'token_type': instance.tokenType,
      'session_id': instance.sessionId,
    };
