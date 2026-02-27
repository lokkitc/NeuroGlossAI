import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../themes/domain/entities/app_theme_entity.dart';
import '../../../themes/presentation/controllers/theme_controllers.dart';
import '../../../themes/presentation/theme_data_builder.dart';
import '../../domain/entities/character.dart';
import '../../../posts/presentation/controllers/posts_controllers.dart';
import '../../../posts/domain/entities/post.dart';

final _characterChatThemeProvider = FutureProvider.family<AppThemeEntity?, String?>((ref, themeId) async {
  final id = (themeId ?? '').trim();
  if (id.isEmpty) return null;

  final repo = ref.read(themesRepositoryProvider);
  final themes = await repo.listAvailable(skip: 0, limit: 200);
  for (final t in themes) {
    if (t.id == id) return t;
  }
  return null;
});

final _publicPostsByCharacterProvider = FutureProvider.family<List<PostEntity>, String>((ref, characterId) async {
  final repo = ref.read(postsRepositoryProvider);
  return repo.listPublicByCharacter(characterId: characterId, skip: 0, limit: 50);
});

class CharacterDetailsPage extends ConsumerWidget {
  const CharacterDetailsPage({super.key, required this.character});

  final CharacterEntity character;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final baseTheme = Theme.of(context);
    final scheme = baseTheme.colorScheme;

    final chatThemeValue = ref.watch(_characterChatThemeProvider(character.chatThemeId));
    final postsValue = ref.watch(_publicPostsByCharacterProvider(character.id));

    final themedChild = Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            pinned: true,
            expandedHeight: 220,
            flexibleSpace: FlexibleSpaceBar(
              title: Text(
                character.displayName,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              background: _Banner(character: character),
            ),
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _Avatar(character: character),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              character.slug,
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                            ),
                            const SizedBox(height: 6),
                            Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: [
                                _Badge(
                                  text: character.isPublic ? 'Public' : 'Private',
                                  bg: character.isPublic ? scheme.primaryContainer : scheme.surfaceContainerHighest,
                                  fg: character.isPublic ? scheme.onPrimaryContainer : scheme.onSurface,
                                ),
                                _Badge(
                                  text: character.isNsfw ? 'NSFW' : 'SFW',
                                  bg: character.isNsfw ? scheme.errorContainer : scheme.surfaceContainerHighest,
                                  fg: character.isNsfw ? scheme.onErrorContainer : scheme.onSurface,
                                ),
                                if ((character.voiceProvider ?? '').trim().isNotEmpty)
                                  _Badge(
                                    text: 'Voice: ${character.voiceProvider}',
                                    bg: scheme.secondaryContainer,
                                    fg: scheme.onSecondaryContainer,
                                  ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 18),
                  if (character.description.trim().isNotEmpty) ...[
                    Text('Description', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    Text(character.description),
                    const SizedBox(height: 18),
                  ],
                  if ((character.greeting ?? '').trim().isNotEmpty) ...[
                    Text('Greeting', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    Text(character.greeting!),
                    const SizedBox(height: 18),
                  ],
                  if ((character.tags ?? const <String>[]).isNotEmpty) ...[
                    Text('Tags', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (final t in character.tags!)
                          Chip(
                            label: Text(t),
                            visualDensity: VisualDensity.compact,
                          ),
                      ],
                    ),
                    const SizedBox(height: 18),
                  ],
                  Text('System prompt', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  _LongTextBox(text: character.systemPrompt),
                  const SizedBox(height: 18),
                  if ((character.stylePrompt ?? '').trim().isNotEmpty) ...[
                    Text('Style prompt', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    _LongTextBox(text: character.stylePrompt!),
                    const SizedBox(height: 18),
                  ],
                  Text('Posts', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 10),
                  postsValue.when(
                    loading: () => const Padding(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      child: Center(child: CircularProgressIndicator()),
                    ),
                    error: (e, _) => Text(e.toString()),
                    data: (posts) {
                      if (posts.isEmpty) return const Text('No posts yet');

                      return ListView.separated(
                        physics: const NeverScrollableScrollPhysics(),
                        shrinkWrap: true,
                        itemCount: posts.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 10),
                        itemBuilder: (context, index) {
                          final p = posts[index];
                          final mediaUrl = p.media.isNotEmpty ? p.media.first.url : null;

                          return Card(
                            child: Padding(
                              padding: const EdgeInsets.all(12),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    character.displayName,
                                    style: Theme.of(context).textTheme.labelMedium?.copyWith(color: scheme.onSurfaceVariant),
                                  ),
                                  const SizedBox(height: 6),
                                  Text(
                                    p.title.isEmpty ? 'Post' : p.title,
                                    style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
                                  ),
                                  if (p.content.isNotEmpty) ...[
                                    const SizedBox(height: 6),
                                    Text(p.content),
                                  ],
                                  if (mediaUrl != null) ...[
                                    const SizedBox(height: 10),
                                    ClipRRect(
                                      borderRadius: BorderRadius.circular(14),
                                      child: AspectRatio(
                                        aspectRatio: 16 / 9,
                                        child: Image.network(
                                          mediaUrl,
                                          fit: BoxFit.cover,
                                          errorBuilder: (_, __, ___) => Container(
                                            color: scheme.surfaceContainerHighest,
                                            alignment: Alignment.center,
                                            child: const Text('Image failed to load'),
                                          ),
                                        ),
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          );
                        },
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );

    return chatThemeValue.when(
      loading: () => themedChild,
      error: (_, __) => themedChild,
      data: (t) {
        if (t == null) return themedChild;

        final light = ThemeDataBuilder.buildOrFallback(
          tokens: t.lightTokens,
          fallback: baseTheme,
          brightness: Brightness.light,
        );
        final dark = ThemeDataBuilder.buildOrFallback(
          tokens: t.darkTokens,
          fallback: baseTheme,
          brightness: Brightness.dark,
        );

        final data = (baseTheme.brightness == Brightness.dark) ? dark : light;
        return Theme(data: data, child: themedChild);
      },
    );
  }
}

class _Banner extends StatelessWidget {
  const _Banner({required this.character});

  final CharacterEntity character;

  @override
  Widget build(BuildContext context) {
    final url = (character.bannerUrl ?? character.thumbnailUrl ?? '').trim();
    if (url.isEmpty) {
      return Container(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
      );
    }

    return Stack(
      fit: StackFit.expand,
      children: [
        Image.network(
          url,
          fit: BoxFit.cover,
          webHtmlElementStrategy: WebHtmlElementStrategy.prefer,
          errorBuilder: (_, __, ___) {
            return Container(color: Theme.of(context).colorScheme.surfaceContainerHighest);
          },
        ),
        DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Colors.black.withValues(alpha: 0.10),
                Colors.black.withValues(alpha: 0.55),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar({required this.character});

  final CharacterEntity character;

  @override
  Widget build(BuildContext context) {
    final url = (character.avatarUrl ?? character.thumbnailUrl ?? '').trim();
    final scheme = Theme.of(context).colorScheme;

    return CircleAvatar(
      radius: 28,
      backgroundColor: scheme.secondaryContainer,
      foregroundColor: scheme.onSecondaryContainer,
      child: url.isNotEmpty
          ? ClipOval(
              child: Image.network(
                url,
                width: 56,
                height: 56,
                fit: BoxFit.cover,
                webHtmlElementStrategy: WebHtmlElementStrategy.prefer,
                errorBuilder: (_, __, ___) => Center(
                  child: Text(
                    character.displayName.isEmpty ? '?' : character.displayName.characters.first.toUpperCase(),
                  ),
                ),
              ),
            )
          : Text(character.displayName.isEmpty ? '?' : character.displayName.characters.first.toUpperCase()),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.text, required this.bg, required this.fg});

  final String text;
  final Color bg;
  final Color fg;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        text,
        style: Theme.of(context).textTheme.labelMedium?.copyWith(color: fg, fontWeight: FontWeight.w700),
      ),
    );
  }
}

class _LongTextBox extends StatelessWidget {
  const _LongTextBox({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: scheme.outlineVariant),
      ),
      child: Text(text),
    );
  }
}
