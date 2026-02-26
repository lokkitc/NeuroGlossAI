import '../../domain/entities/app_theme_entity.dart';
import '../../domain/repositories/themes_repository.dart';
import '../datasources/themes_remote_data_source.dart';
import '../mappers/theme_mapper.dart';

class ThemesRepositoryImpl implements ThemesRepository {
  ThemesRepositoryImpl(this._remote);

  final ThemesRemoteDataSource _remote;

  @override
  Future<List<AppThemeEntity>> listAvailable({String? themeType, int skip = 0, int limit = 50}) async {
    final dtos = await _remote.listAvailable(themeType: themeType, skip: skip, limit: limit);
    return dtos.map(ThemeMapper.toEntity).toList(growable: false);
  }

  @override
  Future<void> selectMyUiTheme({required String themeId}) async {
    await _remote.selectMyUiTheme(themeId: themeId);
  }
}
