import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../dto/auth_session_dto.dart';
import '../dto/user_dto.dart';

class AuthRemoteDataSource {
  AuthRemoteDataSource(this._client);

  final ApiClient _client;

  Future<AuthSessionDto> login({required String username, required String password}) async {
    final json = await _client.postForm(
      ApiEndpoints.authLogin,
      form: {
        'username': username,
        'password': password,
      },
    );
    return AuthSessionDto.fromJson(json);
  }

  Future<UserDto> me() async {
    final json = await _client.getMap(ApiEndpoints.authMe);
    return UserDto.fromJson(json);
  }

  Future<UserDto> updateMe(Map<String, dynamic> payload) async {
    final json = await _client.patchMap(ApiEndpoints.usersMe, data: payload);
    return UserDto.fromJson(json);
  }

  Future<AuthSessionDto> refresh({required String refreshToken}) async {
    final json = await _client.postMap(
      ApiEndpoints.authRefresh,
      data: {'refresh_token': refreshToken},
    );
    return AuthSessionDto.fromJson(json);
  }

  Future<void> logout({required String refreshToken}) async {
    await _client.postMap(
      ApiEndpoints.authLogout,
      data: {'refresh_token': refreshToken},
    );
  }
}
