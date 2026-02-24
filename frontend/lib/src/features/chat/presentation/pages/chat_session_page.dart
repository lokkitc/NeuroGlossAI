import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/widgets/animated_list_item.dart';
import '../../../../core/widgets/error_state.dart';
import '../../../../core/widgets/empty_state.dart';
import '../../../../core/widgets/skeleton_list.dart';
import '../controllers/chat_controllers.dart';

class ChatSessionPage extends ConsumerStatefulWidget {
  const ChatSessionPage({super.key, required this.sessionId});

  final String sessionId;

  @override
  ConsumerState<ChatSessionPage> createState() => _ChatSessionPageState();
}

class _ChatSessionPageState extends ConsumerState<ChatSessionPage> with SingleTickerProviderStateMixin {
  final _composer = TextEditingController();
  final _scrollController = ScrollController();
  int _lastTurnCount = 0;

  @override
  void dispose() {
    _composer.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    if (!_scrollController.hasClients) return;
    final pos = _scrollController.position.maxScrollExtent;
    _scrollController.animateTo(
      pos,
      duration: const Duration(milliseconds: 260),
      curve: Curves.easeOutCubic,
    );
  }

  @override
  Widget build(BuildContext context) {
    final asyncDetail = ref.watch(chatSessionProvider(widget.sessionId));
    final asyncLessons = ref.watch(chatLessonsProvider(widget.sessionId));

    return asyncDetail.when(
      loading: () => const Scaffold(body: SkeletonList()),
      error: (e, _) => Scaffold(
        appBar: AppBar(title: const Text('Chat')),
        body: ErrorState(
          message: e.toString(),
          onRetry: () => ref.read(chatSessionProvider(widget.sessionId).notifier).refresh(),
        ),
      ),
      data: (detail) {
        if (detail.turns.length != _lastTurnCount) {
          _lastTurnCount = detail.turns.length;
          WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
        }

        final titleText = detail.session.title.isEmpty ? 'Chat' : detail.session.title;
        return DefaultTabController(
          length: 2,
          child: Scaffold(
            appBar: AppBar(
              title: Row(
                children: [
                  Hero(
                    tag: 'chat-avatar-${detail.session.id}',
                    child: CircleAvatar(
                      radius: 16,
                      backgroundColor: Theme.of(context).colorScheme.secondaryContainer,
                      foregroundColor: Theme.of(context).colorScheme.onSecondaryContainer,
                      child: Text(titleText.characters.first.toUpperCase()),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Hero(
                      tag: 'chat-title-${detail.session.id}',
                      child: Material(
                        type: MaterialType.transparency,
                        child: Text(titleText, maxLines: 1, overflow: TextOverflow.ellipsis),
                      ),
                    ),
                  ),
                ],
              ),
              bottom: const TabBar(
                tabs: [
                  Tab(text: 'Chat'),
                  Tab(text: 'Lessons'),
                ],
              ),
            ),
            body: TabBarView(
              children: [
                Column(
                  children: [
                    Expanded(
                      child: RefreshIndicator(
                        onRefresh: () => ref.read(chatSessionProvider(widget.sessionId).notifier).refresh(),
                        child: ListView.builder(
                          controller: _scrollController,
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                          itemCount: detail.turns.length,
                          itemBuilder: (context, index) {
                            final t = detail.turns[index];
                            final isUser = t.isUser;
                            return AnimatedListItem(
                              index: index,
                              child: Align(
                                alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                                child: Container(
                                  key: ValueKey(t.id),
                                  constraints: const BoxConstraints(maxWidth: 520),
                                  margin: const EdgeInsets.symmetric(vertical: 6),
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: isUser
                                        ? Theme.of(context).colorScheme.primaryContainer
                                        : Theme.of(context).colorScheme.surfaceContainerHighest,
                                    borderRadius: BorderRadius.circular(16),
                                  ),
                                  child: Text(t.content),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                    ),
                    SafeArea(
                      top: false,
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
                        child: Row(
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _composer,
                                minLines: 1,
                                maxLines: 4,
                                decoration: const InputDecoration(hintText: 'Message...'),
                              ),
                            ),
                            const SizedBox(width: 8),
                            FilledButton(
                              onPressed: () async {
                                final text = _composer.text;
                                _composer.clear();
                                _scrollToBottom();
                                await ref.read(chatSessionProvider(widget.sessionId).notifier).send(text);
                              },
                              child: const Text('Send'),
                            ),
                          ],
                        ),
                      ),
                    )
                  ],
                ),
                asyncLessons.when(
                  loading: () => const SkeletonList(),
                  error: (e, _) => ErrorState(
                    message: e.toString(),
                    onRetry: () => ref.read(chatLessonsProvider(widget.sessionId).notifier).refresh(),
                  ),
                  data: (lessons) {
                    return AnimatedSwitcher(
                      duration: const Duration(milliseconds: 220),
                      switchInCurve: Curves.easeOutCubic,
                      switchOutCurve: Curves.easeInCubic,
                      child: RefreshIndicator(
                        key: ValueKey(lessons.length),
                      onRefresh: () => ref.read(chatLessonsProvider(widget.sessionId).notifier).refresh(),
                      child: ListView(
                        padding: const EdgeInsets.all(12),
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  'Lessons',
                                  style: Theme.of(context).textTheme.titleLarge,
                                ),
                              ),
                              FilledButton.icon(
                                onPressed: () async {
                                  try {
                                    await ref.read(chatLessonsProvider(widget.sessionId).notifier).generate();
                                  } catch (e) {
                                    if (!context.mounted) return;
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(content: Text(e.toString())),
                                    );
                                  }
                                },
                                icon: const Icon(Icons.auto_awesome),
                                label: const Text('Generate'),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          if (lessons.isEmpty)
                            const EmptyState(
                              title: 'No lessons yet',
                              subtitle: 'Tap Generate to create a lesson from the last turns.',
                            )
                          else
                            ...[
                              for (final l in lessons)
                                Card(
                                  child: ListTile(
                                    title: Text(l.title),
                                    subtitle: Text(
                                      l.contentText,
                                      maxLines: 3,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    onTap: () => _showLessonDialog(context, l.title, l.contentText),
                                    trailing: Text(
                                      '${l.sourceTurnFrom}-${l.sourceTurnTo}',
                                      style: Theme.of(context).textTheme.labelMedium,
                                    ),
                                  ),
                                ),
                            ],
                        ],
                      ),
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<void> _showLessonDialog(BuildContext context, String title, String content) async {
    await showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: Text(title),
          content: SingleChildScrollView(child: Text(content)),
          actions: [
            TextButton(onPressed: () => Navigator.of(dialogContext).pop(), child: const Text('Close')),
          ],
        );
      },
    );
  }
}
