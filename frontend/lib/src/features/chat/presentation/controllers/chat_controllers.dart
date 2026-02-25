import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/di/locator.dart';
import '../../../../core/network/api_client.dart';
import '../../data/datasources/chat_remote_data_source.dart';
import '../../data/datasources/chat_learning_remote_data_source.dart';
import '../../data/cache/chat_session_cache.dart';
import '../../data/repositories/chat_learning_repository_impl.dart';
import '../../data/repositories/chat_repository_impl.dart';
import '../../domain/entities/chat_learning_lesson.dart';
import '../../domain/entities/chat_session.dart';
import '../../domain/entities/chat_session_detail.dart';
import '../../domain/entities/chat_turn.dart';
import '../../domain/repositories/chat_learning_repository.dart';
import '../../domain/repositories/chat_repository.dart';

final chatRepositoryProvider = Provider<ChatRepository>((ref) {
  final remote = ChatRemoteDataSource(sl<ApiClient>());
  return ChatRepositoryImpl(remote);
});

final chatLearningRepositoryProvider = Provider<ChatLearningRepository>((ref) {
  final remote = ChatLearningRemoteDataSource(sl<ApiClient>());
  return ChatLearningRepositoryImpl(remote);
});

final chatSessionsProvider = AsyncNotifierProvider<ChatSessionsController, List<ChatSessionEntity>>(ChatSessionsController.new);

class ChatSessionsController extends AsyncNotifier<List<ChatSessionEntity>> {
  @override
  Future<List<ChatSessionEntity>> build() async {
    return ref.read(chatRepositoryProvider).listSessions();
  }
  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => ref.read(chatRepositoryProvider).listSessions());
  }

  Future<ChatSessionEntity> create({String title = '', String? characterId, String? roomId}) async {
    final sess = await ref.read(chatRepositoryProvider).createSession(title: title, characterId: characterId, roomId: roomId);
    final prev = state.valueOrNull ?? const <ChatSessionEntity>[];
    state = AsyncValue.data([sess, ...prev]);
    return sess;
  }
}

final chatLessonsProvider = AsyncNotifierProviderFamily<ChatLessonsController, List<ChatLearningLessonEntity>, String>(
  ChatLessonsController.new,
);

class ChatLessonsController extends FamilyAsyncNotifier<List<ChatLearningLessonEntity>, String> {
  late final String sessionId;

  @override
  Future<List<ChatLearningLessonEntity>> build(String arg) async {
    sessionId = arg;
    return ref.read(chatLearningRepositoryProvider).listLessons(sessionId);
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => ref.read(chatLearningRepositoryProvider).listLessons(sessionId));
  }

  Future<ChatLearningLessonEntity> generate({int turnWindow = 80, String generationMode = 'balanced'}) async {
    final created = await ref
        .read(chatLearningRepositoryProvider)
        .generateLesson(sessionId, turnWindow: turnWindow, generationMode: generationMode);

    final prev = state.valueOrNull ?? const <ChatLearningLessonEntity>[];
    state = AsyncValue.data([created, ...prev]);
    return created;
  }
}

final chatSessionProvider = AsyncNotifierProviderFamily<ChatSessionController, ChatSessionDetailEntity, String>(ChatSessionController.new);

class ChatSessionController extends FamilyAsyncNotifier<ChatSessionDetailEntity, String> {
  late final String sessionId;
  late final ChatSessionCache _cache;

  @override
  Future<ChatSessionDetailEntity> build(String arg) async {
    sessionId = arg;
    _cache = ChatSessionCache();

    final cached = await _cache.load(sessionId);
    if (cached != null) {
      // Serve cache to avoid re-downloading old turns on every open.
      return cached;
    }

    final fresh = await ref.read(chatRepositoryProvider).getSession(sessionId);
    await _cache.save(fresh);
    return fresh;
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final fresh = await ref.read(chatRepositoryProvider).getSession(sessionId);
      await _cache.save(fresh);
      return fresh;
    });
  }

  Future<void> send(String content) async {
    final trimmed = content.trim();
    if (trimmed.isEmpty) return;

    final current = state.valueOrNull;
    if (current == null) {
      await refresh();
      return;
    }

    // Optimistic: show user message immediately.
    final optimisticTurns = [...current.turns];
    final nextIndex = optimisticTurns.isEmpty ? 0 : (optimisticTurns.map((t) => t.turnIndex).reduce((a, b) => a > b ? a : b) + 1);

    final optimistic = ChatSessionDetailEntity(
      session: current.session,
      turns: [
        ...optimisticTurns,
        ChatTurnEntity(
          id: 'optimistic-$nextIndex',
          sessionId: sessionId,
          turnIndex: nextIndex,
          role: 'user',
          content: trimmed,
        ),
      ],
    );
    state = AsyncValue.data(
      optimistic,
    );

    // Best-effort cache update for offline/fast reopen.
    try {
      await _cache.save(optimistic);
    } catch (_) {
      // ignore
    }

    try {
      final inc = await ref.read(chatRepositoryProvider).sendTurn(sessionId: sessionId, content: trimmed);
      // Merge incremental turns into current state by appending.
      final now = state.valueOrNull ?? current;
      final merged = ChatSessionDetailEntity(
        session: inc.session,
        turns: [
          ...now.turns.where((t) => !t.id.startsWith('optimistic-')),
          ...inc.turns,
        ],
      );
      state = AsyncValue.data(merged);
      try {
        await _cache.save(merged);
      } catch (_) {
        // ignore
      }
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}
