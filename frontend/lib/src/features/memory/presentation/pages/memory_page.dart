import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/widgets/animated_list_item.dart';
import '../../../../core/widgets/empty_state.dart';
import '../../../../core/widgets/error_state.dart';
import '../../../../core/widgets/skeleton_list.dart';
import '../../domain/entities/memory_item.dart';
import '../controllers/memory_controllers.dart';

class MemoryPage extends ConsumerWidget {
  const MemoryPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mem = ref.watch(myMemoryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Memory Wallet'),
        actions: [
          IconButton(
            onPressed: () => _showCreateDialog(context, ref),
            icon: const Icon(Icons.add),
            tooltip: 'Add memory',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.read(myMemoryProvider.notifier).refresh(),
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 220),
          switchInCurve: Curves.easeOutCubic,
          switchOutCurve: Curves.easeInCubic,
          child: mem.when(
            loading: () => const SkeletonList(key: ValueKey('loading')),
            error: (e, _) => ErrorState(
              key: const ValueKey('error'),
              message: e.toString(),
              onRetry: () => ref.read(myMemoryProvider.notifier).refresh(),
            ),
            data: (data) {
              if (data.isEmpty) {
                return const EmptyState(
                  key: ValueKey('empty'),
                  title: 'No memories yet',
                  subtitle: 'Add preferences like “Talk more aggressive” or “Call me Alex”.',
                );
              }

              return ListView.separated(
                key: const ValueKey('list'),
                padding: const EdgeInsets.all(12),
                itemCount: data.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (context, index) {
                  final item = data[index];
                  final title = item.title.trim().isEmpty ? 'Memory' : item.title.trim();

                  return AnimatedListItem(
                    index: index,
                    child: ListTile(
                      title: Text(title),
                      subtitle: Text(item.content, maxLines: 2, overflow: TextOverflow.ellipsis),
                      leading: Icon(item.isPinned ? Icons.push_pin : Icons.push_pin_outlined),
                      trailing: Wrap(
                        spacing: 4,
                        children: [
                          IconButton(
                            tooltip: item.isEnabled ? 'Disable' : 'Enable',
                            onPressed: () => ref.read(myMemoryProvider.notifier).updateItem(item, isEnabled: !item.isEnabled),
                            icon: Icon(item.isEnabled ? Icons.visibility : Icons.visibility_off),
                          ),
                          IconButton(
                            tooltip: item.isPinned ? 'Unpin' : 'Pin',
                            onPressed: () => ref.read(myMemoryProvider.notifier).updateItem(item, isPinned: !item.isPinned),
                            icon: Icon(item.isPinned ? Icons.star : Icons.star_border),
                          ),
                          IconButton(
                            tooltip: 'Edit',
                            onPressed: () => _showEditDialog(context, ref, item),
                            icon: const Icon(Icons.edit_outlined),
                          ),
                          IconButton(
                            tooltip: 'Delete',
                            onPressed: () => _confirmDelete(context, ref, item.id),
                            icon: const Icon(Icons.delete_outline),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              );
            },
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showCreateDialog(context, ref),
        child: const Icon(Icons.add),
      ),
    );
  }

  Future<void> _showCreateDialog(BuildContext context, WidgetRef ref) async {
    final titleController = TextEditingController();
    final contentController = TextEditingController();
    bool pinned = true;
    bool enabled = true;

    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setState) {
            return AlertDialog(
              title: const Text('Add memory'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: titleController,
                    decoration: const InputDecoration(labelText: 'Title (optional)'),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: contentController,
                    minLines: 2,
                    maxLines: 5,
                    decoration: const InputDecoration(labelText: 'Preference / fact'),
                  ),
                  const SizedBox(height: 12),
                  SwitchListTile(
                    value: enabled,
                    onChanged: (v) => setState(() => enabled = v),
                    title: const Text('Enabled'),
                    contentPadding: EdgeInsets.zero,
                  ),
                  SwitchListTile(
                    value: pinned,
                    onChanged: (v) => setState(() => pinned = v),
                    title: const Text('Pinned'),
                    contentPadding: EdgeInsets.zero,
                  ),
                ],
              ),
              actions: [
                TextButton(onPressed: () => Navigator.of(dialogContext).pop(false), child: const Text('Cancel')),
                FilledButton(onPressed: () => Navigator.of(dialogContext).pop(true), child: const Text('Save')),
              ],
            );
          },
        );
      },
    );

    if (ok != true) return;
    final content = contentController.text.trim();
    if (content.isEmpty) return;

    await ref.read(myMemoryProvider.notifier).create(
          title: titleController.text.trim(),
          content: content,
          isPinned: pinned,
          isEnabled: enabled,
        );
  }

  Future<void> _showEditDialog(BuildContext context, WidgetRef ref, MemoryItemEntity item) async {
    final titleController = TextEditingController(text: item.title);
    final contentController = TextEditingController(text: item.content);

    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Edit memory'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: titleController,
                decoration: const InputDecoration(labelText: 'Title (optional)'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: contentController,
                minLines: 2,
                maxLines: 6,
                decoration: const InputDecoration(labelText: 'Preference / fact'),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(dialogContext).pop(false), child: const Text('Cancel')),
            FilledButton(onPressed: () => Navigator.of(dialogContext).pop(true), child: const Text('Save')),
          ],
        );
      },
    );

    if (ok != true) return;

    await ref.read(myMemoryProvider.notifier).updateItem(
          item,
          title: titleController.text.trim(),
          content: contentController.text.trim(),
        );
  }

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref, String id) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Delete memory?'),
          content: const Text('This will remove the memory item.'),
          actions: [
            TextButton(onPressed: () => Navigator.of(dialogContext).pop(false), child: const Text('Cancel')),
            FilledButton(onPressed: () => Navigator.of(dialogContext).pop(true), child: const Text('Delete')),
          ],
        );
      },
    );

    if (ok != true) return;
    await ref.read(myMemoryProvider.notifier).delete(id);
  }
}
