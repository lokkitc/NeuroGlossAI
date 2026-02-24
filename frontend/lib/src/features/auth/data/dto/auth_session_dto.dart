import 'package:json_annotation/json_annotation.dart';

part 'auth_session_dto.g.dart';

@JsonSerializable(fieldRename: FieldRename.snake)
class AuthSessionDto {
  const AuthSessionDto({
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
    required this.sessionId,
  });

  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final String sessionId;

  factory AuthSessionDto.fromJson(Map<String, dynamic> json) => _$AuthSessionDtoFromJson(json);
  Map<String, dynamic> toJson() => _$AuthSessionDtoToJson(this);
}
