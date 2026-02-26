import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/presentation/controllers/auth_controller.dart';
import '../controllers/theme_controllers.dart';

final availableThemesProvider = FutureProvider((ref) async {
  final repo = ref.watch(themesRepositoryProvider);
  return repo.listAvailable(skip: 0, limit: 200);
});

class ThemeSelectPage extends ConsumerWidget {
  const ThemeSelectPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider).valueOrNull;
    final selectedThemeId = auth?.user?.selectedThemeId;

    final themesValue = ref.watch(availableThemesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Themes'),
      ),
      body: themesValue.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text(e.toString())),
        data: (themes) {
          if (themes.isEmpty) {
            return const Center(child: Text('No themes available'));
          }

          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
            itemCount: themes.length,
            separatorBuilder: (_, __) => const SizedBox(height: 10),
            itemBuilder: (context, i) {
              final t = themes[i];
              final isSelected = t.id == selectedThemeId;

              return Card(
                child: ListTile(
                  leading: Icon(isSelected ? Icons.radio_button_checked : Icons.radio_button_off),
                  title: Text(t.displayName),
                  subtitle: Text(t.slug),
                  trailing: isSelected ? const Icon(Icons.check) : null,
                  onTap: () async {
                    await ref.read(themeControllerProvider.notifier).selectMyUiTheme(themeId: t.id);
                    ref.invalidate(availableThemesProvider);
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Selected: ${t.displayName}')));
                    }
                  },
                ),
              );
            },
          );
        },
      ),
    );
  }
}
