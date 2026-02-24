import 'package:dio/dio.dart';

import 'app_exception.dart';

class ErrorMapper {
  static AppException map(Object error) {
    if (error is AppException) return error;

    if (error is DioException) {
      final status = error.response?.statusCode;
      if (status == 401) {
        return const UnauthorizedException('Unauthorized');
      }
      final msg = _safeMessage(error);
      return NetworkException(msg, statusCode: status);
    }

    return UnexpectedException(error.toString());
  }

  static String _safeMessage(DioException e) {
    final data = e.response?.data;
    if (data is Map && data['message'] is String) return data['message'] as String;
    if (data is Map && data['detail'] is String) return data['detail'] as String;
    return e.message ?? 'Network error';
  }
}
