abstract class AppException implements Exception {
  const AppException(this.message);
  final String message;

  @override
  String toString() => '$runtimeType: $message';
}

class NetworkException extends AppException {
  const NetworkException(super.message, {this.statusCode});
  final int? statusCode;
}

class UnauthorizedException extends AppException {
  const UnauthorizedException(super.message);
}

class UnexpectedException extends AppException {
  const UnexpectedException(super.message);
}
