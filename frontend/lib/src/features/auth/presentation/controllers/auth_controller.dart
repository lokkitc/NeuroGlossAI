import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/di/locator.dart';
import '../../../../core/errors/app_exception.dart';
import '../../domain/repositories/auth_repository.dart';
import '../../domain/usecases/get_current_user.dart';
import '../../domain/usecases/login.dart';
import '../../domain/usecases/logout.dart';
import '../../domain/usecases/update_me.dart';
import 'auth_state.dart';

final authControllerProvider = AsyncNotifierProvider<AuthController, AuthState>(AuthController.new);

class AuthController extends AsyncNotifier<AuthState> {
  final _streamController = StreamController<void>.broadcast();

  Stream<void> get stream => _streamController.stream;

  @override
  Future<AuthState> build() async {
    ref.onDispose(() {
      _streamController.close();
    });

    // Auto-login if token exists.
    final repo = sl.get<AuthRepository>();
    final has = await repo.hasToken();
    if (!has) {
      return const AuthState(isAuthenticated: false);
    }

    try {
      final user = await sl.get<GetCurrentUserUseCase>()();
      return AuthState(isAuthenticated: true, user: user);
    } on UnauthorizedException {
      await repo.logout();
      return const AuthState(isAuthenticated: false);
    } catch (_) {
      // Keep app usable; user can login again.
      return const AuthState(isAuthenticated: false);
    }
  }

  Future<void> login({required String username, required String password}) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      await sl.get<LoginUseCase>()(username: username, password: password);
      final user = await sl.get<GetCurrentUserUseCase>()();
      if (!_streamController.isClosed) {
        _streamController.add(null);
      }
      return AuthState(isAuthenticated: true, user: user);
    });
  }

  Future<void> logout() async {
    await sl.get<LogoutUseCase>()();
    if (!_streamController.isClosed) {
      _streamController.add(null);
    }
    state = const AsyncValue.data(AuthState(isAuthenticated: false));
  }

  Future<void> updateProfile({
    String? avatarUrl,
    String? thumbnailUrl,
    String? bannerUrl,
    String? preferredName,
    String? bio,
    String? timezone,
    String? uiTheme,
    String? assistantTone,
    int? assistantVerbosity,
    Map<String, dynamic>? preferences,
    String? targetLanguage,
    String? nativeLanguage,
    List<String>? interests,
  }) async {
    final current = state.valueOrNull;
    if (current == null || !current.isAuthenticated) return;

    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final user = await sl.get<UpdateMeUseCase>()(
            avatarUrl: avatarUrl,
            thumbnailUrl: thumbnailUrl,
            bannerUrl: bannerUrl,
            preferredName: preferredName,
            bio: bio,
            timezone: timezone,
            uiTheme: uiTheme,
            assistantTone: assistantTone,
            assistantVerbosity: assistantVerbosity,
            preferences: preferences,
            targetLanguage: targetLanguage,
            nativeLanguage: nativeLanguage,
            interests: interests,
          );
      if (!_streamController.isClosed) {
        _streamController.add(null);
      }
      return AuthState(isAuthenticated: true, user: user);
    });
  }
}
