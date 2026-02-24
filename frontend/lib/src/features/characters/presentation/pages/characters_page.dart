import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/routes.dart';
import '../../../../core/widgets/animated_list_item.dart';
import '../../../../core/widgets/empty_state.dart';
import '../../../../core/widgets/error_state.dart';
import '../../../../core/widgets/skeleton_list.dart';
import '../controllers/characters_controller.dart';

class CharactersPage extends ConsumerWidget {
  const CharactersPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final chars = ref.watch(myCharactersProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Characters')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push(Routes.characterCreate),
        child: const Icon(Icons.add),
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.read(myCharactersProvider.notifier).refresh(),
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 220),
          switchInCurve: Curves.easeOutCubic,
          switchOutCurve: Curves.easeInCubic,
          child: chars.when(
            loading: () => const SkeletonList(key: ValueKey('loading')),
            error: (e, _) => ErrorState(
              key: const ValueKey('error'),
              message: e.toString(),
              onRetry: () => ref.read(myCharactersProvider.notifier).refresh(),
            ),
            data: (data) {
              if (data.isEmpty) {
                return const EmptyState(
                  key: ValueKey('empty'),
                  title: 'No characters',
                  subtitle: 'Create your first character.',
                );
              }
              return ListView.separated(
                key: const ValueKey('list'),
                padding: const EdgeInsets.all(12),
                itemBuilder: (context, index) {
                  final c = data[index];
                  return AnimatedListItem(
                    index: index,
                    child: ListTile(
                      title: Text(c.displayName),
                      subtitle: Text(c.slug),
                      trailing: IconButton(
                        icon: const Icon(Icons.delete_outline),
                        onPressed: () => ref.read(myCharactersProvider.notifier).delete(c.id),
                      ),
                    ),
                  );
                },
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemCount: data.length,
              );
            },
          ),
        ),
      ),
    );
  }
}
