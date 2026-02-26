import '../entities/app_theme_entity.dart';

abstract class ThemesRepository {
  Future<List<AppThemeEntity>> listAvailable({String? themeType, int skip, int limit});
  Future<void> selectMyUiTheme({required String themeId});
}
