import 'package:equatable/equatable.dart';

class AuthSession extends Equatable {
  const AuthSession({required this.accessToken, required this.refreshToken, required this.sessionId});

  final String accessToken;
  final String refreshToken;
  final String sessionId;

  @override
  List<Object?> get props => [accessToken, refreshToken, sessionId];
}
