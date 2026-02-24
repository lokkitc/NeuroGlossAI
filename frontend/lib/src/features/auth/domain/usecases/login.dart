import '../entities/auth_session.dart';
import '../repositories/auth_repository.dart';

class LoginUseCase {
  const LoginUseCase(this._repo);
  final AuthRepository _repo;

  Future<AuthSession> call({required String username, required String password}) {
    return _repo.login(username: username, password: password);
  }
}
