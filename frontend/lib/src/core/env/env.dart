import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter/foundation.dart';
import 'dart:io';

class Env {
  const Env({
    required this.apiBaseUrl,
    required this.apiPrefix,
    required this.logNetwork,
  });

  final String apiBaseUrl;
  final String apiPrefix;
  final bool logNetwork;

  String get apiRoot {
    final base = _normalizeBaseUrl(apiBaseUrl);
    return base.replaceFirst(RegExp(r'/*$'), '') + apiPrefix;
  }

  String _normalizeBaseUrl(String input) {
    // Android emulator can't access host machine via localhost.
    // Use 10.0.2.2 instead.
    if (!kIsWeb && Platform.isAndroid) {
      return input
          .replaceFirst('http://localhost', 'http://10.0.2.2')
          .replaceFirst('http://127.0.0.1', 'http://10.0.2.2')
          .replaceFirst('https://localhost', 'https://10.0.2.2')
          .replaceFirst('https://127.0.0.1', 'https://10.0.2.2');
    }
    return input;
  }

  static String fileForFlavor(String flavor) {
    switch (flavor) {
      case 'prod':
        return 'assets/env/.env.prod';
      case 'dev':
      default:
        return 'assets/env/.env.dev';
    }
  }

  static Env fromDotenv() {
    final base = dotenv.get('API_BASE_URL');
    final prefix = dotenv.get('API_PREFIX', fallback: '/api/v1');
    final log = dotenv.get('LOG_NETWORK', fallback: 'false').toLowerCase() == 'true';
    return Env(apiBaseUrl: base, apiPrefix: prefix, logNetwork: log);
  }
}
