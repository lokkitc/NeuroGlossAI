import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../auth/presentation/controllers/auth_controller.dart';
import '../../../../core/widgets/animated_counter.dart';
import '../../../../core/widgets/animated_list_item.dart';
import '../../../../core/widgets/empty_state.dart';
import '../../../../core/widgets/error_state.dart';
import '../../../../core/widgets/skeleton_list.dart';
import '../../../../core/constants/routes.dart';
import '../../../chat/presentation/controllers/chat_controllers.dart';
import '../../../memory/presentation/controllers/memory_controllers.dart';

class HomePage extends ConsumerWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final chatsCount = ref.watch(chatSessionsProvider).valueOrNull?.length ?? 0;
    final memoryCount = ref.watch(myMemoryProvider).valueOrNull?.length ?? 0;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Home'),
        actions: [
          IconButton(
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
            icon: const Icon(Icons.logout),
            tooltip: 'Logout',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(authControllerProvider);
          await ref.read(authControllerProvider.future);
        },
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 220),
          switchInCurve: Curves.easeOutCubic,
          switchOutCurve: Curves.easeInCubic,
          child: auth.when(
            loading: () => const SkeletonList(key: ValueKey('loading')),
            error: (e, _) => ErrorState(key: const ValueKey('error'), message: e.toString()),
            data: (data) {
              final user = data.user;
              if (user == null) {
                return const EmptyState(key: ValueKey('empty'), title: 'No user', subtitle: 'Please login again.');
              }

              return ListView(
                key: const ValueKey('data'),
                padding: const EdgeInsets.all(16),
                children: [
                  Text('Hi, ${user.username}', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 6),
                  Text(user.email, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Theme.of(context).hintColor)),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: Card(
                          child: Padding(
                            padding: const EdgeInsets.all(14),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Chats'),
                                const SizedBox(height: 8),
                                AnimatedCounter(value: chatsCount),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Card(
                          child: Padding(
                            padding: const EdgeInsets.all(14),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Memories'),
                                const SizedBox(height: 8),
                                AnimatedCounter(value: memoryCount),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 18),
                  AnimatedListItem(
                    index: 0,
                    child: _QuickActionCard(
                      title: 'Start chatting',
                      subtitle: 'Create a chat session and talk to your character.',
                      icon: Icons.chat_bubble,
                      onTap: () => context.go(Routes.chats),
                    ),
                  ),
                  const SizedBox(height: 12),
                  AnimatedListItem(
                    index: 1,
                    child: _QuickActionCard(
                      title: 'Your characters',
                      subtitle: 'Create characters and manage personalities.',
                      icon: Icons.person,
                      onTap: () => context.go(Routes.characters),
                    ),
                  ),
                  const SizedBox(height: 12),
                  AnimatedListItem(
                    index: 2,
                    child: _QuickActionCard(
                      title: 'Memory wallet',
                      subtitle: 'Pin facts and preferences for the assistant.',
                      icon: Icons.memory,
                      onTap: () => context.go(Routes.memory),
                    ),
                  ),
                  const SizedBox(height: 12),
                  AnimatedListItem(
                    index: 3,
                    child: _QuickActionCard(
                      title: 'Public posts',
                      subtitle: 'Share updates with media and explore the feed.',
                      icon: Icons.public,
                      onTap: () => context.go(Routes.posts),
                    ),
                  ),
                  const SizedBox(height: 12),
                  AnimatedListItem(
                    index: 4,
                    child: _QuickActionCard(
                      title: 'People',
                      subtitle: 'Find users and view public profiles.',
                      icon: Icons.people,
                      onTap: () => context.go(Routes.publicUsers),
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}

class _QuickActionCard extends StatelessWidget {
  const _QuickActionCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.onTap,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Icon(icon, size: 28),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 4),
                    Text(subtitle, style: Theme.of(context).textTheme.bodyMedium),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}
