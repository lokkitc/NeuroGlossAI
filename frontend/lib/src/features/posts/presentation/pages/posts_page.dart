import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/routes.dart';
import '../../../../core/widgets/error_state.dart';
import '../../../../core/widgets/skeleton_list.dart';
import '../controllers/posts_controllers.dart';

class PostsPage extends ConsumerWidget {
  const PostsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncPosts = ref.watch(publicPostsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Posts'),
        actions: [
          IconButton(
            onPressed: () => context.go(Routes.myPosts),
            icon: const Icon(Icons.person_outline),
            tooltip: 'My posts',
          ),
          IconButton(
            onPressed: () => context.go(Routes.postCreate),
            icon: const Icon(Icons.add),
            tooltip: 'Create',
          ),
        ],
      ),
      body: asyncPosts.when(
        loading: () => const SkeletonList(),
        error: (e, _) => ErrorState(
          message: e.toString(),
          onRetry: () => ref.read(publicPostsProvider.notifier).refresh(),
        ),
        data: (posts) {
          if (posts.isEmpty) {
            return const Center(child: Text('No posts yet'));
          }

          return RefreshIndicator(
            onRefresh: () => ref.read(publicPostsProvider.notifier).refresh(),
            child: ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: posts.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, index) {
                final p = posts[index];
                final mediaUrl = p.media.isNotEmpty ? p.media.first.url : null;
                final isBotPost = (p.characterId ?? '').trim().isNotEmpty;
                final displayName = (isBotPost ? (p.characterDisplayName ?? '').trim() : (p.authorUsername ?? '').trim());
                final fallbackName = displayName.isNotEmpty ? displayName : (isBotPost ? 'Character' : 'User');
                final avatarUrl = (isBotPost ? p.characterAvatarUrl : p.authorAvatarUrl);

                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            CircleAvatar(
                              radius: 16,
                              child: (avatarUrl ?? '').trim().isNotEmpty
                                  ? ClipOval(
                                      child: Image.network(
                                        avatarUrl!.trim(),
                                        width: 32,
                                        height: 32,
                                        fit: BoxFit.cover,
                                        webHtmlElementStrategy: WebHtmlElementStrategy.prefer,
                                        errorBuilder: (_, __, ___) => Center(
                                          child: Text(fallbackName.characters.first.toUpperCase()),
                                        ),
                                      ),
                                    )
                                  : Text(fallbackName.characters.first.toUpperCase()),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          fallbackName,
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                          style: Theme.of(context).textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w800),
                                        ),
                                      ),
                                      Text(
                                        p.isPublic ? 'PUBLIC' : 'PRIVATE',
                                        style: Theme.of(context).textTheme.labelSmall,
                                      ),
                                    ],
                                  ),
                                  if ((p.title).trim().isNotEmpty)
                                    Text(
                                      p.title,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: Theme.of(context).textTheme.bodySmall,
                                    ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                p.title.isEmpty ? 'Post' : p.title,
                                style: Theme.of(context).textTheme.titleMedium,
                              ),
                            ),
                            const SizedBox.shrink(),
                          ],
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
                                webHtmlElementStrategy: WebHtmlElementStrategy.prefer,
                                errorBuilder: (_, __, ___) => Container(
                                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                                  alignment: Alignment.center,
                                  child: const Text('Image failed to load'),
                                ),
                              ),
                            ),
                          ),
                        ],
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            OutlinedButton.icon(
                              onPressed: () async {
                                try {
                                  await ref.read(publicPostsProvider.notifier).like(p.id);
                                  if (!context.mounted) return;
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Liked')));
                                } catch (e) {
                                  if (!context.mounted) return;
                                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
                                }
                              },
                              icon: const Icon(Icons.thumb_up_alt_outlined),
                              label: const Text('Like'),
                            ),
                            const SizedBox(width: 10),
                            OutlinedButton.icon(
                              onPressed: () async {
                                try {
                                  await ref.read(publicPostsProvider.notifier).unlike(p.id);
                                  if (!context.mounted) return;
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Unliked')));
                                } catch (e) {
                                  if (!context.mounted) return;
                                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
                                }
                              },
                              icon: const Icon(Icons.thumb_down_alt_outlined),
                              label: const Text('Unlike'),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
