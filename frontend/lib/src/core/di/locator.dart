import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get_it/get_it.dart';
import 'package:logger/logger.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';

import '../env/env.dart';
import '../logging/app_logger.dart';
import '../network/api_client.dart';
import '../network/auth_token_interceptor.dart';
import '../network/token_storage.dart';
import '../../features/auth/data/datasources/auth_remote_data_source.dart';
import '../../features/auth/data/repositories/auth_repository_impl.dart';
import '../../features/auth/domain/repositories/auth_repository.dart';
import '../../features/auth/domain/usecases/get_current_user.dart';
import '../../features/auth/domain/usecases/login.dart';
import '../../features/auth/domain/usecases/logout.dart';
import '../../features/auth/domain/usecases/update_me.dart';

final sl = GetIt.I;

void setupLocator(Env env) {
  sl
    ..registerSingleton<Env>(env)
    ..registerLazySingleton<Logger>(() => Logger(printer: PrettyPrinter(methodCount: 0)))
    ..registerLazySingleton<AppLogger>(() => AppLogger(sl<Logger>()))
    ..registerLazySingleton<FlutterSecureStorage>(() => const FlutterSecureStorage())
    ..registerLazySingleton<TokenStorage>(() => TokenStorage(sl<FlutterSecureStorage>()))
    ..registerLazySingleton<Dio>(() {
      final dio = Dio(
        BaseOptions(
          baseUrl: env.apiRoot,
          connectTimeout: const Duration(seconds: 30),
          receiveTimeout: const Duration(seconds: 30),
          sendTimeout: const Duration(seconds: 30),
          headers: {
            'Accept': 'application/json',
          },
        ),
      );

      // Debug: log actual URL
      print('API Base URL: ${env.apiRoot}');

      dio.interceptors.add(AuthTokenInterceptor(dio, sl<TokenStorage>()));
      if (env.logNetwork) {
        dio.interceptors.add(
          PrettyDioLogger(
            requestHeader: false,
            requestBody: false,
            responseHeader: false,
            responseBody: true,
            compact: true,
            maxWidth: 120,
          ),
        );
      }

      return dio;
    })
    ..registerLazySingleton<ApiClient>(() => ApiClient(sl<Dio>()))

    // Auth feature
    ..registerLazySingleton<AuthRemoteDataSource>(() => AuthRemoteDataSource(sl<ApiClient>()))
    ..registerLazySingleton<AuthRepositoryImpl>(() => AuthRepositoryImpl(sl<AuthRemoteDataSource>(), sl<TokenStorage>()))
    ..registerLazySingleton<AuthRepository>(() => sl<AuthRepositoryImpl>())
    ..registerLazySingleton<LoginUseCase>(() => LoginUseCase(sl<AuthRepository>()))
    ..registerLazySingleton<GetCurrentUserUseCase>(() => GetCurrentUserUseCase(sl<AuthRepository>()))
    ..registerLazySingleton<UpdateMeUseCase>(() => UpdateMeUseCase(sl<AuthRepository>()))
    ..registerLazySingleton<LogoutUseCase>(() => LogoutUseCase(sl<AuthRepository>()));
}
