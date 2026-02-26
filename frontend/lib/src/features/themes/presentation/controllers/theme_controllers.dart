import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/di/locator.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/network/api_client.dart';
import '../../../auth/presentation/controllers/auth_controller.dart';
import '../../../auth/domain/usecases/get_current_user.dart';
import '../../data/datasources/themes_remote_data_source.dart';
import '../../data/repositories/themes_repository_impl.dart';
import '../../domain/entities/app_theme_entity.dart';
import '../../domain/repositories/themes_repository.dart';
import '../theme_data_builder.dart';

final themesRepositoryProvider = Provider<ThemesRepository>((ref) {
  final remote = ThemesRemoteDataSource(sl<ApiClient>());
  return ThemesRepositoryImpl(remote);
});

class ThemeState {
  const ThemeState({
    required this.lightTheme,
    required this.darkTheme,
    required this.themeMode,
    this.selectedTheme,
  });

  final ThemeData lightTheme;
  final ThemeData darkTheme;
  final ThemeMode themeMode;
  final AppThemeEntity? selectedTheme;
}

final themeControllerProvider = AsyncNotifierProvider<ThemeController, ThemeState>(ThemeController.new);

class ThemeController extends AsyncNotifier<ThemeState> {
  @override
  Future<ThemeState> build() async {
    final auth = ref.watch(authControllerProvider).valueOrNull;
    final selectedThemeId = auth?.user?.selectedThemeId;

    var light = _fallbackLight();
    var dark = _fallbackDark();

    AppThemeEntity? selected;

    if (selectedThemeId != null && selectedThemeId.isNotEmpty) {
      try {
        final themes = await ref.read(themesRepositoryProvider).listAvailable(skip: 0, limit: 200);
        for (final t in themes) {
          if (t.id == selectedThemeId) {
            selected = t;
            break;
          }
        }

        if (selected != null) {
          light = ThemeDataBuilder.buildOrFallback(
            tokens: selected.lightTokens,
            fallback: light,
            brightness: Brightness.light,
          );
          dark = ThemeDataBuilder.buildOrFallback(
            tokens: selected.darkTokens,
            fallback: dark,
            brightness: Brightness.dark,
          );
        }
      } catch (_) {
        // Keep fallbacks.
      }
    }

    return ThemeState(
      lightTheme: light,
      darkTheme: dark,
      themeMode: _mapUiTheme(auth?.user?.uiTheme),
      selectedTheme: selected,
    );
  }

  Future<void> selectMyUiTheme({required String themeId}) async {
    final repo = ref.read(themesRepositoryProvider);
    await repo.selectMyUiTheme(themeId: themeId);

    // Refresh auth user to sync selected_theme_id.
    await sl.get<GetCurrentUserUseCase>()();
    ref.invalidate(authControllerProvider);
    ref.invalidateSelf();
  }

  ThemeMode _mapUiTheme(String? uiTheme) {
    switch ((uiTheme ?? 'system').toLowerCase()) {
      case 'light':
        return ThemeMode.light;
      case 'dark':
        return ThemeMode.dark;
      default:
        return ThemeMode.system;
    }
  }

  ThemeData _fallbackLight() {
    return AppTheme.light;
  }

  ThemeData _fallbackDark() {
    return AppTheme.dark;
  }
}
