import '../../domain/entities/user.dart';

class AuthState {
  const AuthState({required this.isAuthenticated, this.user});

  final bool isAuthenticated;
  final UserEntity? user;
}
