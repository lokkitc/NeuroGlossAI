import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/di/locator.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/widgets/empty_state.dart';
import '../../../../core/widgets/error_state.dart';
import '../../data/datasources/public_users_remote_data_source.dart';
import '../../data/mappers/public_user_mapper.dart';
import '../../domain/entities/public_user.dart';

final _publicUsersRemoteProvider = Provider<PublicUsersRemoteDataSource>((ref) {
  return PublicUsersRemoteDataSource(sl<ApiClient>());
});

final publicUsersQueryProvider = StateProvider<String>((ref) => '');

final publicUsersProvider = FutureProvider<List<PublicUserEntity>>((ref) async {
  final q = ref.watch(publicUsersQueryProvider).trim();
  final list = await ref.read(_publicUsersRemoteProvider).listUsers(q: q.isEmpty ? null : q, skip: 0, limit: 50);
  return list.map(PublicUserMapper.fromJson).toList(growable: false);
});

class PublicUsersPage extends ConsumerStatefulWidget {
  const PublicUsersPage({super.key});

  @override
  ConsumerState<PublicUsersPage> createState() => _PublicUsersPageState();
}

class _PublicUsersPageState extends ConsumerState<PublicUsersPage> {
  final _controller = TextEditingController();
  Timer? _debounce;

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _onQueryChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 250), () {
      ref.read(publicUsersQueryProvider.notifier).state = value;
    });
  }

  @override
  Widget build(BuildContext context) {
    final usersValue = ref.watch(publicUsersProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('People'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
            child: TextField(
              controller: _controller,
              onChanged: _onQueryChanged,
              textInputAction: TextInputAction.search,
              decoration: InputDecoration(
                hintText: 'Search by username',
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
              ),
            ),
          ),
          Expanded(
            child: usersValue.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => ErrorState(message: e.toString()),
              data: (users) {
                if (users.isEmpty) {
                  return const EmptyState(title: 'No users', subtitle: 'Try another search query.');
                }

                return ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                  itemCount: users.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (context, index) {
                    final u = users[index];
                    final title = (u.preferredName ?? '').trim().isNotEmpty ? u.preferredName!.trim() : u.username;
                    final subtitle = (u.bio ?? '').trim().isNotEmpty ? u.bio!.trim() : '@${u.username}';
                    final avatar = (u.avatarUrl ?? u.thumbnailUrl ?? '').trim();

                    return Card(
                      child: ListTile(
                        leading: CircleAvatar(
                          child: avatar.isNotEmpty
                              ? ClipOval(
                                  child: Image.network(
                                    avatar,
                                    width: 40,
                                    height: 40,
                                    fit: BoxFit.cover,
                                    webHtmlElementStrategy: WebHtmlElementStrategy.prefer,
                                    errorBuilder: (_, __, ___) => Center(
                                      child: Text(
                                        u.username.isEmpty ? '?' : u.username.characters.first.toUpperCase(),
                                      ),
                                    ),
                                  ),
                                )
                              : Text(u.username.isEmpty ? '?' : u.username.characters.first.toUpperCase()),
                        ),
                        title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
                        subtitle: Text(subtitle, maxLines: 2, overflow: TextOverflow.ellipsis),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () {
                          if (u.username.isEmpty) return;
                          context.push('/u/${u.username}');
                        },
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
