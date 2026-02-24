import '../entities/user.dart';
import '../repositories/auth_repository.dart';

class GetCurrentUserUseCase {
  const GetCurrentUserUseCase(this._repo);
  final AuthRepository _repo;

  Future<UserEntity> call() => _repo.me();
}
