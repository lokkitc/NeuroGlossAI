import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/widgets/animated_list_item.dart';
import '../../../../core/widgets/empty_state.dart';
import '../../../../core/widgets/error_state.dart';
import '../../../../core/widgets/skeleton_list.dart';
import '../../../characters/presentation/controllers/characters_controller.dart';
import '../controllers/chat_controllers.dart';

class ChatsPage extends ConsumerWidget {
  const ChatsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sessions = ref.watch(chatSessionsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Chats')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _createSession(context, ref),
        child: const Icon(Icons.add),
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.read(chatSessionsProvider.notifier).refresh(),
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 220),
          switchInCurve: Curves.easeOutCubic,
          switchOutCurve: Curves.easeInCubic,
          child: sessions.when(
            loading: () => const SkeletonList(key: ValueKey('loading')),
            error: (e, _) => ErrorState(
              key: const ValueKey('error'),
              message: e.toString(),
              onRetry: () => ref.read(chatSessionsProvider.notifier).refresh(),
            ),
            data: (data) {
              if (data.isEmpty) {
                return const EmptyState(
                  key: ValueKey('empty'),
                  title: 'No chats yet',
                  subtitle: 'Create a chat session to start talking.',
                );
              }
              return ListView.separated(
                key: const ValueKey('list'),
                padding: const EdgeInsets.all(12),
                itemBuilder: (context, index) {
                  final s = data[index];
                  final title = s.title.isEmpty ? 'Chat session' : s.title;
                  return AnimatedListItem(
                    index: index,
                    child: ListTile(
                      leading: Hero(
                        tag: 'chat-avatar-${s.id}',
                        child: CircleAvatar(
                          backgroundColor: Theme.of(context).colorScheme.secondaryContainer,
                          foregroundColor: Theme.of(context).colorScheme.onSecondaryContainer,
                          child: Text(title.isEmpty ? 'C' : title.characters.first.toUpperCase()),
                        ),
                      ),
                      title: Hero(
                        tag: 'chat-title-${s.id}',
                        child: Material(
                          type: MaterialType.transparency,
                          child: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
                        ),
                      ),
                      subtitle: Text(s.id),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => context.push('/chats/${s.id}'),
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

  Future<void> _createSession(BuildContext context, WidgetRef ref) async {
    // Ensure we have characters to attach.
    final chars = ref.read(myCharactersProvider).valueOrNull;
    if (chars == null || chars.isEmpty) {
      final messenger = ScaffoldMessenger.of(context);
      messenger.clearSnackBars();
      messenger.showSnackBar(
        SnackBar(
          content: const Text('Create a character first.'),
          action: SnackBarAction(
            label: 'Create',
            onPressed: () => context.push('/characters/create'),
          ),
        ),
      );
      return;
    }

    String? selected = chars.first.id;
    final titleController = TextEditingController();

    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('New chat'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: titleController,
                decoration: const InputDecoration(labelText: 'Title (optional)'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: selected,
                items: [
                  for (final c in chars)
                    DropdownMenuItem(value: c.id, child: Text(c.displayName)),
                ],
                onChanged: (v) => selected = v,
                decoration: const InputDecoration(labelText: 'Character'),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(dialogContext).pop(false), child: const Text('Cancel')),
            FilledButton(onPressed: () => Navigator.of(dialogContext).pop(true), child: const Text('Create')),
          ],
        );
      },
    );

    if (ok != true) return;

    final sess = await ref.read(chatSessionsProvider.notifier).create(
          title: titleController.text.trim(),
          characterId: selected,
        );
    if (!context.mounted) return;
    context.push('/chats/${sess.id}');
  }
}
