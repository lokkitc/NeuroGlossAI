import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../controllers/posts_controllers.dart';

class MyPostsPage extends ConsumerWidget {
  const MyPostsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final postsValue = ref.watch(myPostsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Posts'),
        actions: [
          IconButton(
            onPressed: () => ref.read(myPostsProvider.notifier).refresh(),
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: postsValue.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text(e.toString())),
        data: (posts) {
          if (posts.isEmpty) return const Center(child: Text('No posts yet'));

          return ListView.separated(
            padding: const EdgeInsets.all(12),
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
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              p.title.isEmpty ? 'Post' : p.title,
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                          ),
                          FilledButton(
                            onPressed: () async {
                              try {
                                await ref.read(myPostsProvider.notifier).setPublic(postId: p.id, isPublic: !p.isPublic);
                                if (!context.mounted) return;
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text(!p.isPublic ? 'Shared' : 'Unshared')),
                                );
                              } catch (e) {
                                if (!context.mounted) return;
                                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
                              }
                            },
                            child: Text(p.isPublic ? 'Unshare' : 'Share'),
                          ),
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
                      Text(
                        p.isPublic ? 'PUBLIC' : 'PRIVATE',
                        style: Theme.of(context).textTheme.labelSmall,
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
