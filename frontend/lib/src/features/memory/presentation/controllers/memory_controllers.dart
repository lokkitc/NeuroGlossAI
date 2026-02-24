import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/di/locator.dart';
import '../../../../core/network/api_client.dart';
import '../../data/datasources/memory_remote_data_source.dart';
import '../../data/repositories/memory_repository_impl.dart';
import '../../domain/entities/memory_item.dart';
import '../../domain/repositories/memory_repository.dart';

final memoryRepositoryProvider = Provider<MemoryRepository>((ref) {
  final remote = MemoryRemoteDataSource(sl<ApiClient>());
  return MemoryRepositoryImpl(remote);
});

final myMemoryProvider = AsyncNotifierProvider<MyMemoryController, List<MemoryItemEntity>>(MyMemoryController.new);

class MyMemoryController extends AsyncNotifier<List<MemoryItemEntity>> {
  @override
  Future<List<MemoryItemEntity>> build() async {
    return ref.read(memoryRepositoryProvider).listMy();
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => ref.read(memoryRepositoryProvider).listMy());
  }

  Future<MemoryItemEntity> create({
    String title = '',
    required String content,
    bool isPinned = false,
    bool isEnabled = true,
    List<String>? tags,
    int importance = 0,
  }) async {
    final created = await ref.read(memoryRepositoryProvider).create(
          title: title,
          content: content,
          isPinned: isPinned,
          isEnabled: isEnabled,
          tags: tags,
          importance: importance,
        );

    final prev = state.valueOrNull ?? const <MemoryItemEntity>[];
    state = AsyncValue.data([created, ...prev]);
    return created;
  }

  Future<MemoryItemEntity> updateItem(
    MemoryItemEntity item, {
    String? title,
    String? content,
    bool? isPinned,
    bool? isEnabled,
    List<String>? tags,
    int? importance,
  }) async {
    final updated = await ref.read(memoryRepositoryProvider).update(
          item.id,
          title: title,
          content: content,
          isPinned: isPinned,
          isEnabled: isEnabled,
          tags: tags,
          importance: importance,
        );

    final prev = state.valueOrNull ?? const <MemoryItemEntity>[];
    state = AsyncValue.data([
      for (final x in prev) if (x.id == item.id) updated else x,
    ]);

    return updated;
  }

  Future<void> delete(String id) async {
    await ref.read(memoryRepositoryProvider).delete(id);
    final prev = state.valueOrNull ?? const <MemoryItemEntity>[];
    state = AsyncValue.data(prev.where((x) => x.id != id).toList(growable: false));
  }
}
