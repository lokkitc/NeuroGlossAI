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
                padding: const EdgeInsets.fromLTRB(12, 12, 12, 20),
                itemBuilder: (context, index) {
                  final c = data[index];
                  return AnimatedListItem(
                    index: index,
                    child: _CharacterCard(
                      character: c,
                      onTap: () => context.push('/characters/${c.id}'),
                      onDelete: () => ref.read(myCharactersProvider.notifier).delete(c.id),
                    ),
                  );
                },
                separatorBuilder: (_, __) => const SizedBox(height: 12),
                itemCount: data.length,
              );
            },
          ),
        ),
      ),
    );
  }
}

class _CharacterCard extends StatelessWidget {
  const _CharacterCard({
    required this.character,
    required this.onTap,
    required this.onDelete,
  });

  final dynamic character;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final avatarUrl = (character.avatarUrl ?? character.thumbnailUrl ?? '').toString().trim();
    final bannerUrl = (character.bannerUrl ?? character.thumbnailUrl ?? '').toString().trim();
    final tags = (character.tags as List?)?.cast<String>() ?? const <String>[];

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (bannerUrl.isNotEmpty)
              SizedBox(
                height: 92,
                width: double.infinity,
                child: Image.network(
                  bannerUrl,
                  fit: BoxFit.cover,
                  webHtmlElementStrategy: WebHtmlElementStrategy.prefer,
                  errorBuilder: (_, __, ___) => Container(color: scheme.surfaceContainerHighest),
                ),
              ),
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 12, 12, 12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  CircleAvatar(
                    radius: 22,
                    backgroundColor: scheme.secondaryContainer,
                    foregroundColor: scheme.onSecondaryContainer,
                    child: avatarUrl.isNotEmpty
                        ? ClipOval(
                            child: Image.network(
                              avatarUrl,
                              width: 44,
                              height: 44,
                              fit: BoxFit.cover,
                              webHtmlElementStrategy: WebHtmlElementStrategy.prefer,
                              errorBuilder: (_, __, ___) => Center(
                                child: Text(
                                  (character.displayName as String).isEmpty
                                      ? '?'
                                      : (character.displayName as String).characters.first.toUpperCase(),
                                ),
                              ),
                            ),
                          )
                        : Text(
                            (character.displayName as String).isEmpty
                                ? '?'
                                : (character.displayName as String).characters.first.toUpperCase(),
                          ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                character.displayName as String,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.delete_outline),
                              onPressed: onDelete,
                              tooltip: 'Delete',
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          character.slug as String,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                        ),
                        if ((character.description as String).trim().isNotEmpty) ...[
                          const SizedBox(height: 8),
                          Text(
                            character.description as String,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                        ],
                        const SizedBox(height: 10),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            _MiniBadge(
                              text: character.isPublic == true ? 'Public' : 'Private',
                              bg: character.isPublic == true ? scheme.primaryContainer : scheme.surfaceContainerHighest,
                              fg: character.isPublic == true ? scheme.onPrimaryContainer : scheme.onSurface,
                            ),
                            _MiniBadge(
                              text: character.isNsfw == true ? 'NSFW' : 'SFW',
                              bg: character.isNsfw == true ? scheme.errorContainer : scheme.surfaceContainerHighest,
                              fg: character.isNsfw == true ? scheme.onErrorContainer : scheme.onSurface,
                            ),
                            if (tags.isNotEmpty) _MiniBadge(text: '#${tags.first}', bg: scheme.secondaryContainer, fg: scheme.onSecondaryContainer),
                            if (tags.length > 1)
                              _MiniBadge(text: '+${tags.length - 1}', bg: scheme.surfaceContainerHighest, fg: scheme.onSurfaceVariant),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MiniBadge extends StatelessWidget {
  const _MiniBadge({required this.text, required this.bg, required this.fg});

  final String text;
  final Color bg;
  final Color fg;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999)),
      child: Text(
        text,
        style: Theme.of(context).textTheme.labelMedium?.copyWith(color: fg, fontWeight: FontWeight.w800),
      ),
    );
  }
}
