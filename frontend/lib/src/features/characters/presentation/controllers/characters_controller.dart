import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/di/locator.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/uploads_remote_data_source.dart';
import '../../data/datasources/characters_remote_data_source.dart';
import '../../data/repositories/characters_repository_impl.dart';
import '../../domain/entities/character.dart';
import '../../domain/repositories/characters_repository.dart';

final charactersRepositoryProvider = Provider<CharactersRepository>((ref) {
  // Feature-scoped DI (keeps core locator minimal)
  final remote = CharactersRemoteDataSource(sl<ApiClient>());
  return CharactersRepositoryImpl(remote);
});

final uploadsRemoteDataSourceProvider = Provider<UploadsRemoteDataSource>((ref) {
  return UploadsRemoteDataSource(sl<ApiClient>());
});

final myCharactersProvider = AsyncNotifierProvider<MyCharactersController, List<CharacterEntity>>(MyCharactersController.new);

class MyCharactersController extends AsyncNotifier<List<CharacterEntity>> {
  @override
  Future<List<CharacterEntity>> build() async {
    return ref.read(charactersRepositoryProvider).listMy();
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => ref.read(charactersRepositoryProvider).listMy());
  }

  Future<void> delete(String id) async {
    final prev = state.valueOrNull ?? const <CharacterEntity>[];
    state = AsyncValue.data(prev.where((c) => c.id != id).toList(growable: false));
    try {
      await ref.read(charactersRepositoryProvider).delete(id);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}
