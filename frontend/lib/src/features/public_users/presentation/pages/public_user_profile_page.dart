import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/di/locator.dart';
import '../../../../core/network/api_client.dart';
import '../../../themes/domain/entities/app_theme_entity.dart';
import '../../../themes/presentation/controllers/theme_controllers.dart';
import '../../../themes/presentation/theme_data_builder.dart';
import '../../data/datasources/public_users_remote_data_source.dart';
import '../../data/mappers/public_user_mapper.dart';
import '../../domain/entities/public_user.dart';
import 'public_user_posts_provider.dart';

final _publicUsersRemoteProvider = Provider<PublicUsersRemoteDataSource>((ref) {
  return PublicUsersRemoteDataSource(sl<ApiClient>());
});

final publicUserByUsernameProvider = FutureProvider.family<PublicUserEntity, String>((ref, username) async {
  final json = await ref.read(_publicUsersRemoteProvider).getByUsername(username: username);
  return PublicUserMapper.fromJson(json);
});

final _publicUserThemeProvider = FutureProvider.family<AppThemeEntity?, String?>((ref, themeId) async {
  final id = (themeId ?? '').trim();
  if (id.isEmpty) return null;

  final repo = ref.read(themesRepositoryProvider);
  final themes = await repo.listAvailable(themeType: 'USER', skip: 0, limit: 200);
  for (final t in themes) {
    if (t.id == id) return t;
  }
  return null;
});

class PublicUserProfilePage extends ConsumerWidget {
  const PublicUserProfilePage({super.key, required this.username});

  final String username;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userValue = ref.watch(publicUserByUsernameProvider(username));

    return userValue.when(
      loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (e, _) => Scaffold(appBar: AppBar(title: const Text('Profile')), body: Center(child: Text(e.toString()))),
      data: (user) {
        final baseTheme = Theme.of(context);
        final scheme = baseTheme.colorScheme;

        final postsValue = ref.watch(publicPostsByUserProvider(user.username));

        final themedPage = Scaffold(
          body: CustomScrollView(
            slivers: [
              SliverAppBar(
                pinned: true,
                expandedHeight: 220,
                flexibleSpace: FlexibleSpaceBar(
                  title: Text(user.preferredName?.isNotEmpty == true ? user.preferredName! : user.username),
                  background: _Banner(url: user.bannerUrl ?? user.thumbnailUrl),
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
                          _Avatar(url: user.avatarUrl ?? user.thumbnailUrl, fallback: user.username),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  user.preferredName?.isNotEmpty == true ? user.preferredName! : user.username,
                                  style: baseTheme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  '@${user.username}',
                                  style: baseTheme.textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                                ),
                                if ((user.bio ?? '').trim().isNotEmpty) ...[
                                  const SizedBox(height: 10),
                                  Text(user.bio!),
                                ],
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        decoration: BoxDecoration(
                          color: scheme.surfaceContainerLowest,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: scheme.outlineVariant),
                        ),
                        child: Row(
                          children: [
                            Expanded(child: _Stat(label: 'Posts', value: postsValue.valueOrNull?.length ?? 0)),
                            Expanded(child: _Stat(label: 'Followers', value: 0)),
                            Expanded(child: _Stat(label: 'Following', value: 0)),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text('Posts', style: baseTheme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
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
                              final isBotPost = (p.characterId ?? '').trim().isNotEmpty;
                              final authorLine = isBotPost ? (p.characterId ?? 'Character') : user.username;

                              return Card(
                                child: Padding(
                                  padding: const EdgeInsets.all(12),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        authorLine,
                                        style: baseTheme.textTheme.labelMedium?.copyWith(color: scheme.onSurfaceVariant),
                                      ),
                                      const SizedBox(height: 6),
                                      Text(
                                        p.title.isEmpty ? 'Post' : p.title,
                                        style: baseTheme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
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

        final themeValue = ref.watch(_publicUserThemeProvider(user.selectedThemeId));
        return themeValue.when(
          loading: () => themedPage,
          error: (_, __) => themedPage,
          data: (t) {
            if (t == null) return themedPage;

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
            return Theme(data: data, child: themedPage);
          },
        );
      },
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value});

  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text('$value', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 2),
        Text(label, style: theme.textTheme.labelMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
      ],
    );
  }
}

class _Banner extends StatelessWidget {
  const _Banner({required this.url});

  final String? url;

  @override
  Widget build(BuildContext context) {
    final u = (url ?? '').trim();
    if (u.isEmpty) {
      return Container(color: Theme.of(context).colorScheme.surfaceContainerHighest);
    }
    return Image.network(
      u,
      fit: BoxFit.cover,
      webHtmlElementStrategy: WebHtmlElementStrategy.prefer,
      errorBuilder: (_, __, ___) => Container(color: Theme.of(context).colorScheme.surfaceContainerHighest),
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar({required this.url, required this.fallback});

  final String? url;
  final String fallback;

  @override
  Widget build(BuildContext context) {
    final u = (url ?? '').trim();
    final scheme = Theme.of(context).colorScheme;

    return CircleAvatar(
      radius: 28,
      backgroundColor: scheme.secondaryContainer,
      foregroundColor: scheme.onSecondaryContainer,
      child: u.isNotEmpty
          ? ClipOval(
              child: Image.network(
                u,
                width: 56,
                height: 56,
                fit: BoxFit.cover,
                webHtmlElementStrategy: WebHtmlElementStrategy.prefer,
                errorBuilder: (_, __, ___) => Center(
                  child: Text(fallback.isEmpty ? '?' : fallback.characters.first.toUpperCase()),
                ),
              ),
            )
          : Text(fallback.isEmpty ? '?' : fallback.characters.first.toUpperCase()),
    );
  }
}
