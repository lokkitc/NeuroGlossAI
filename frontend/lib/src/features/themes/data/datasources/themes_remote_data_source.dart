import '../../../../core/network/api_client.dart';
import '../dto/app_theme_dto.dart';

class ThemesRemoteDataSource {
  ThemesRemoteDataSource(this._client);

  final ApiClient _client;

  Future<List<AppThemeDto>> listAvailable({String? themeType, int skip = 0, int limit = 50}) async {
    final json = await _client.getList(
      '/themes/available',
      query: {
        if (themeType != null) 'theme_type': themeType,
        'skip': skip,
        'limit': limit,
      },
    );

    return json.map((e) => AppThemeDto.fromJson(Map<String, dynamic>.from(e as Map))).toList(growable: false);
  }

  Future<Map<String, dynamic>> selectMyUiTheme({required String themeId}) {
    return _client.postMap('/themes/me/select', data: {'theme_id': themeId});
  }
}
