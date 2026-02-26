import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../routing/app_router.dart';
import '../core/theme/app_theme.dart';
import '../features/themes/presentation/controllers/theme_controllers.dart';

class App extends ConsumerWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    final theme = ref.watch(themeControllerProvider).valueOrNull;

    return MaterialApp.router(
      title: 'NeuroGlossAI',
      theme: theme?.lightTheme ?? AppTheme.light,
      darkTheme: theme?.darkTheme ?? AppTheme.dark,
      themeMode: theme?.themeMode ?? ThemeMode.system,
      routerConfig: router,
    );
  }
}
