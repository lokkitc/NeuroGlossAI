import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../domain/entities/app_theme_entity.dart';

class ThemeDataBuilder {
  static ThemeData buildOrFallback({
    required ThemeTokensEntity? tokens,
    required ThemeData fallback,
    required Brightness brightness,
  }) {
    if (tokens == null) return fallback;

    final palette = tokens.palette;

    final primary = _tryParseColor(palette['primary']);
    final secondary = _tryParseColor(palette['secondary']);
    final background = _tryParseColor(palette['background']);
    final surface = _tryParseColor(palette['surface']);

    if (primary == null) return fallback;

    final baseScheme = ColorScheme.fromSeed(seedColor: primary, brightness: brightness);

    final scheme = baseScheme.copyWith(
      primary: primary,
      secondary: secondary ?? baseScheme.secondary,
      surface: surface ?? baseScheme.surface,
    );

    final scaffoldBg = background ?? scheme.surface;

    return AppTheme.buildFromScheme(brightness: brightness, scheme: scheme, scaffoldBackgroundColor: scaffoldBg);
  }

  static Color? _tryParseColor(dynamic raw) {
    if (raw == null) return null;
    if (raw is int) return Color(raw);
    if (raw is String) {
      final s = raw.trim();
      if (s.isEmpty) return null;

      if (s.startsWith('#')) {
        final hex = s.substring(1);
        if (hex.length == 6) {
          final v = int.tryParse('FF$hex', radix: 16);
          if (v == null) return null;
          return Color(v);
        }
        if (hex.length == 8) {
          final v = int.tryParse(hex, radix: 16);
          if (v == null) return null;
          return Color(v);
        }
      }

      if (s.startsWith('0x')) {
        final v = int.tryParse(s.substring(2), radix: 16);
        if (v == null) return null;
        return Color(v);
      }

      final v = int.tryParse(s, radix: 10);
      if (v != null) return Color(v);
    }

    return null;
  }
}
