import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/constants/route_names.dart';
import '../core/constants/routes.dart';
import '../features/auth/presentation/controllers/auth_controller.dart';
import '../features/auth/presentation/pages/login_page.dart';
import '../app/app_shell.dart';
import '../features/chat/presentation/pages/chats_page.dart';
import '../features/chat/presentation/pages/chat_session_page.dart';
import '../features/characters/presentation/pages/characters_page.dart';
import '../features/characters/presentation/pages/character_create_page.dart';
import '../features/home/presentation/pages/home_page.dart';
import '../features/posts/presentation/pages/posts_page.dart';
import '../features/posts/presentation/pages/post_create_page.dart';
import '../features/memory/presentation/pages/memory_page.dart';
import '../features/profile/presentation/pages/profile_page.dart';
import '../features/splash/presentation/pages/splash_page.dart';
import '../features/themes/presentation/pages/theme_select_page.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final auth = ref.watch(authControllerProvider);

  return GoRouter(
    initialLocation: Routes.splash,
    refreshListenable: GoRouterRefreshStream(ref.watch(authControllerProvider.notifier).stream),
    redirect: (context, state) {
      final location = state.matchedLocation;
      final authState = auth;

      final isLoggingIn = location == Routes.login;

      // While loading, keep splash.
      if (authState.isLoading) {
        return location == Routes.splash ? null : Routes.splash;
      }

      final isAuthed = authState.valueOrNull?.isAuthenticated ?? false;

      if (!isAuthed) {
        return isLoggingIn ? null : Routes.login;
      }

      if (isLoggingIn || location == Routes.splash) {
        return Routes.home;
      }

      return null;
    },
    routes: [
      GoRoute(
        path: Routes.splash,
        name: RouteNames.splash,
        builder: (context, state) => const SplashPage(),
      ),
      GoRoute(
        path: Routes.login,
        name: RouteNames.login,
        builder: (context, state) => const LoginPage(),
      ),
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) => AppShell(navigationShell: navigationShell),
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: Routes.home,
                name: RouteNames.home,
                builder: (context, state) => const HomePage(),
                routes: [
                  GoRoute(
                    path: 'posts',
                    name: RouteNames.posts,
                    builder: (context, state) => const PostsPage(),
                    routes: [
                      GoRoute(
                        path: 'create',
                        name: RouteNames.postCreate,
                        builder: (context, state) => const PostCreatePage(),
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: Routes.chats,
                name: RouteNames.chats,
                builder: (context, state) => const ChatsPage(),
                routes: [
                  GoRoute(
                    path: ':sessionId',
                    name: RouteNames.chatSession,
                    builder: (context, state) {
                      final id = state.pathParameters['sessionId'] ?? '';
                      return ChatSessionPage(sessionId: id);
                    },
                  ),
                ],
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: Routes.characters,
                name: RouteNames.characters,
                builder: (context, state) => const CharactersPage(),
                routes: [
                  GoRoute(
                    path: 'create',
                    name: RouteNames.characterCreate,
                    builder: (context, state) => const CharacterCreatePage(),
                  ),
                ],
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: Routes.memory,
                name: RouteNames.memory,
                builder: (context, state) => const MemoryPage(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: Routes.profile,
                name: RouteNames.profile,
                builder: (context, state) => const ProfilePage(),
                routes: [
                  GoRoute(
                    path: 'themes',
                    name: RouteNames.themeSelect,
                    builder: (context, state) => const ThemeSelectPage(),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    ],
  );
});

class GoRouterRefreshStream extends ChangeNotifier {
  GoRouterRefreshStream(Stream<dynamic> stream) {
    notifyListeners();
    _subscription = stream.asBroadcastStream().listen((_) => notifyListeners());
  }

  late final StreamSubscription<dynamic> _subscription;

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
