import 'package:dio/dio.dart';

import 'token_storage.dart';

class AuthTokenInterceptor extends Interceptor {
  AuthTokenInterceptor(this._dio, this._tokenStorage);

  final Dio _dio;
  final TokenStorage _tokenStorage;

  Future<void>? _refreshing;

  @override
  Future<void> onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await _tokenStorage.readAccessToken();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }

    final deviceId = await _tokenStorage.ensureDeviceId();
    options.headers['X-Device-Id'] = deviceId;

    final sessionId = await _tokenStorage.readSessionId();
    if (sessionId != null && sessionId.isNotEmpty) {
      options.headers['X-Session-Id'] = sessionId;
    }
    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    final status = err.response?.statusCode;
    final req = err.requestOptions;
    final alreadyRetried = (req.extra['__retried'] == true);

    if (status == 401 && !alreadyRetried) {
      final refreshToken = await _tokenStorage.readRefreshToken();
      if (refreshToken != null && refreshToken.isNotEmpty) {
        try {
          _refreshing ??= _doRefresh(refreshToken);
          await _refreshing;
          _refreshing = null;

          final newAccess = await _tokenStorage.readAccessToken();
          final newReq = _cloneOptions(req);
          newReq.extra['__retried'] = true;
          if (newAccess != null && newAccess.isNotEmpty) {
            newReq.headers['Authorization'] = 'Bearer $newAccess';
          }
          final res = await _dio.fetch<dynamic>(newReq);
          handler.resolve(res);
          return;
        } catch (_) {
          try {
            await _tokenStorage.clear();
          } catch (_) {}
        } finally {
          _refreshing = null;
        }
      }
    }

    handler.next(err);
  }

  Future<void> _doRefresh(String refreshToken) async {
    final dio = Dio(BaseOptions(baseUrl: _dio.options.baseUrl, headers: {'Accept': 'application/json'}));
    final deviceId = await _tokenStorage.ensureDeviceId();
    dio.options.headers['X-Device-Id'] = deviceId;

    final sessionId = await _tokenStorage.readSessionId();
    if (sessionId != null && sessionId.isNotEmpty) {
      dio.options.headers['X-Session-Id'] = sessionId;
    }

    final res = await dio.post<dynamic>('/auth/refresh', data: {'refresh_token': refreshToken});
    final data = res.data;
    if (data is! Map) {
      throw Exception('Invalid refresh response');
    }
    final map = Map<String, dynamic>.from(data);
    final access = (map['access_token'] as String?) ?? '';
    final refresh = (map['refresh_token'] as String?) ?? '';
    final sess = (map['session_id'] as String?) ?? '';

    if (access.isEmpty || refresh.isEmpty) {
      throw Exception('Invalid refresh payload');
    }
    await _tokenStorage.writeAccessToken(access);
    await _tokenStorage.writeRefreshToken(refresh);
    if (sess.isNotEmpty) {
      await _tokenStorage.writeSessionId(sess);
    }
  }

  RequestOptions _cloneOptions(RequestOptions requestOptions) {
    return RequestOptions(
      path: requestOptions.path,
      method: requestOptions.method,
      baseUrl: requestOptions.baseUrl,
      data: requestOptions.data,
      queryParameters: Map<String, dynamic>.from(requestOptions.queryParameters),
      headers: Map<String, dynamic>.from(requestOptions.headers),
      extra: Map<String, dynamic>.from(requestOptions.extra),
      responseType: requestOptions.responseType,
      contentType: requestOptions.contentType,
      followRedirects: requestOptions.followRedirects,
      validateStatus: requestOptions.validateStatus,
      receiveDataWhenStatusError: requestOptions.receiveDataWhenStatusError,
      receiveTimeout: requestOptions.receiveTimeout,
      sendTimeout: requestOptions.sendTimeout,
      connectTimeout: requestOptions.connectTimeout,
      maxRedirects: requestOptions.maxRedirects,
      requestEncoder: requestOptions.requestEncoder,
      responseDecoder: requestOptions.responseDecoder,
      onReceiveProgress: requestOptions.onReceiveProgress,
      onSendProgress: requestOptions.onSendProgress,
    );
  }
}
