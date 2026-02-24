import 'package:logger/logger.dart';

class AppLogger {
  AppLogger(this._logger);

  final Logger _logger;

  void d(String message, [Object? error, StackTrace? stackTrace]) => _logger.d(message, error: error, stackTrace: stackTrace);
  void i(String message, [Object? error, StackTrace? stackTrace]) => _logger.i(message, error: error, stackTrace: stackTrace);
  void w(String message, [Object? error, StackTrace? stackTrace]) => _logger.w(message, error: error, stackTrace: stackTrace);
  void e(String message, [Object? error, StackTrace? stackTrace]) => _logger.e(message, error: error, stackTrace: stackTrace);
}
