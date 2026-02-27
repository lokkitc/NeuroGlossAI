import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../posts/presentation/controllers/posts_controllers.dart';
import '../../../posts/domain/entities/post.dart';

final publicPostsByUserProvider = FutureProvider.family<List<PostEntity>, String>((ref, username) async {
  final repo = ref.read(postsRepositoryProvider);
  return repo.listPublicByUsername(username: username, skip: 0, limit: 50);
});
