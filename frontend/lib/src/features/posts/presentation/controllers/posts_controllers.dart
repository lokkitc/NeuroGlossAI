import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/di/locator.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/uploads_remote_data_source.dart';
import '../../data/datasources/posts_remote_data_source.dart';
import '../../data/repositories/posts_repository_impl.dart';
import '../../domain/entities/post.dart';
import '../../domain/repositories/posts_repository.dart';

final postsRepositoryProvider = Provider<PostsRepository>((ref) {
  final remote = PostsRemoteDataSource(sl<ApiClient>());
  return PostsRepositoryImpl(remote);
});

final uploadsRemoteDataSourceProvider = Provider<UploadsRemoteDataSource>((ref) {
  return UploadsRemoteDataSource(sl<ApiClient>());
});

final publicPostsProvider = AsyncNotifierProvider<PublicPostsController, List<PostEntity>>(PublicPostsController.new);

final myPostsProvider = AsyncNotifierProvider<MyPostsController, List<PostEntity>>(MyPostsController.new);

class PublicPostsController extends AsyncNotifier<List<PostEntity>> {
  @override
  Future<List<PostEntity>> build() async {
    return ref.read(postsRepositoryProvider).listPublic();
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => ref.read(postsRepositoryProvider).listPublic());
  }

  Future<void> like(String postId) async {
    await ref.read(postsRepositoryProvider).like(postId);
  }

  Future<void> unlike(String postId) async {
    await ref.read(postsRepositoryProvider).unlike(postId);
  }
}

class MyPostsController extends AsyncNotifier<List<PostEntity>> {
  @override
  Future<List<PostEntity>> build() async {
    return ref.read(postsRepositoryProvider).listMine();
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => ref.read(postsRepositoryProvider).listMine());
  }

  Future<void> setPublic({required String postId, required bool isPublic}) async {
    await ref.read(postsRepositoryProvider).setPublic(id: postId, isPublic: isPublic);
    await refresh();
  }
}
