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

    final typography = tokens.typography ?? const <String, dynamic>{};
    final components = tokens.components ?? const <String, dynamic>{};
    final effects = tokens.effects ?? const <String, dynamic>{};

    final primary = _tryParseColor(palette['primary']);
    final secondary = _tryParseColor(palette['secondary']);
    final background = _tryParseColor(palette['background']);
    final surface = _tryParseColor(palette['surface']);
    final error = _tryParseColor(palette['error']);
    final textPrimary = _tryParseColor(palette['textPrimary']);
    final textSecondary = _tryParseColor(palette['textSecondary']);
    final border = _tryParseColor(palette['border']);

    if (primary == null) return fallback;

    final baseScheme = ColorScheme.fromSeed(seedColor: primary, brightness: brightness);

    final scheme = baseScheme.copyWith(
      primary: primary,
      secondary: secondary ?? baseScheme.secondary,
      surface: surface ?? baseScheme.surface,
      error: error ?? baseScheme.error,
      onSurface: textPrimary ?? baseScheme.onSurface,
      onPrimary: textPrimary ?? baseScheme.onPrimary,
      onSecondary: textPrimary ?? baseScheme.onSecondary,
      onSurfaceVariant: textSecondary ?? baseScheme.onSurfaceVariant,
      outline: border ?? baseScheme.outline,
    );

    final scaffoldBg = background ?? scheme.surface;

    final base = AppTheme.buildFromScheme(brightness: brightness, scheme: scheme, scaffoldBackgroundColor: scaffoldBg);

    final fontFamily = (typography['fontFamily'] is String) ? (typography['fontFamily'] as String).trim() : null;
    final weightsRaw = _asMap(typography['fontWeights']);
    final sizesRaw = _asMap(typography['fontSizes']);

    final regularW = _tryParseFontWeight(weightsRaw['regular']) ?? FontWeight.w400;
    final mediumW = _tryParseFontWeight(weightsRaw['medium']) ?? FontWeight.w500;
    final semiboldW = _tryParseFontWeight(weightsRaw['semibold']) ?? FontWeight.w600;
    final boldW = _tryParseFontWeight(weightsRaw['bold']) ?? FontWeight.w700;

    final smSize = _tryParseDouble(sizesRaw['sm']);
    final mdSize = _tryParseDouble(sizesRaw['md']);
    final lgSize = _tryParseDouble(sizesRaw['lg']);
    final xlSize = _tryParseDouble(sizesRaw['xl']);
    final xxlSize = _tryParseDouble(sizesRaw['2xl']) ?? _tryParseDouble(sizesRaw['xxl']);

    final textTheme = base.textTheme
        .apply(
          fontFamily: (fontFamily != null && fontFamily.isNotEmpty) ? fontFamily : null,
          bodyColor: scheme.onSurface,
          displayColor: scheme.onSurface,
        )
        .copyWith(
          bodySmall: base.textTheme.bodySmall?.copyWith(
            fontWeight: regularW,
            fontSize: smSize ?? base.textTheme.bodySmall?.fontSize,
          ),
          bodyMedium: base.textTheme.bodyMedium?.copyWith(
            fontWeight: regularW,
            fontSize: mdSize ?? base.textTheme.bodyMedium?.fontSize,
          ),
          bodyLarge: base.textTheme.bodyLarge?.copyWith(
            fontWeight: mediumW,
            fontSize: lgSize ?? base.textTheme.bodyLarge?.fontSize,
          ),
          titleMedium: base.textTheme.titleMedium?.copyWith(
            fontWeight: semiboldW,
            fontSize: lgSize ?? base.textTheme.titleMedium?.fontSize,
          ),
          titleLarge: base.textTheme.titleLarge?.copyWith(
            fontWeight: boldW,
            fontSize: xlSize ?? base.textTheme.titleLarge?.fontSize,
          ),
          headlineSmall: base.textTheme.headlineSmall?.copyWith(
            fontWeight: boldW,
            fontSize: xxlSize ?? base.textTheme.headlineSmall?.fontSize,
          ),
          labelLarge: base.textTheme.labelLarge?.copyWith(
            fontWeight: boldW,
            fontSize: mdSize ?? base.textTheme.labelLarge?.fontSize,
          ),
        );

    final effectsBorderRadius = _asMap(effects['borderRadius']);
    final componentsButton = _asMap(components['button']);
    final componentsCard = _asMap(components['card']);
    final componentsInput = _asMap(components['input']);
    final componentsAppBar = _asMap(components['appBar']);

    final buttonRadius = _tryParseDouble(componentsButton['radius']) ?? _tryParseDouble(effectsBorderRadius['md']);
    final cardRadius = _tryParseDouble(componentsCard['radius']) ?? _tryParseDouble(effectsBorderRadius['lg']);
    final inputRadius = _tryParseDouble(componentsInput['radius']) ?? _tryParseDouble(effectsBorderRadius['md']);

    final effectsShadows = _asMap(effects['shadows']);
    final cardShadow = _asMap(effectsShadows['card']);
    final shadowColorHex = cardShadow['color'];
    final shadowColor = _tryParseColor(shadowColorHex);
    final shadowOpacity = _tryParseDouble(cardShadow['opacity']);
    final cardShadowColor = (shadowColor != null && shadowOpacity != null)
        ? shadowColor.withValues(alpha: shadowOpacity.clamp(0.0, 1.0))
        : shadowColor;

    final centerTitleRaw = componentsAppBar['centerTitle'];
    final centerTitle = (centerTitleRaw is bool) ? centerTitleRaw : null;

    final buttonShape = buttonRadius != null
        ? RoundedRectangleBorder(borderRadius: BorderRadius.circular(buttonRadius))
        : null;
    final cardShape = cardRadius != null
        ? RoundedRectangleBorder(borderRadius: BorderRadius.circular(cardRadius))
        : null;

    final inputBorder = inputRadius != null
        ? OutlineInputBorder(borderRadius: BorderRadius.circular(inputRadius), borderSide: BorderSide.none)
        : null;
    final inputFocusedBorder = inputRadius != null
        ? OutlineInputBorder(
            borderRadius: BorderRadius.circular(inputRadius),
            borderSide: BorderSide(color: scheme.primary, width: 1.4),
          )
        : null;

    return base.copyWith(
      textTheme: textTheme,
      primaryTextTheme: textTheme,
      appBarTheme: base.appBarTheme.copyWith(
        centerTitle: centerTitle ?? base.appBarTheme.centerTitle,
        titleTextStyle: base.appBarTheme.titleTextStyle?.copyWith(
          fontFamily: (fontFamily != null && fontFamily.isNotEmpty) ? fontFamily : null,
          color: scheme.onSurface,
        ),
      ),
      cardTheme: base.cardTheme.copyWith(
        shape: cardShape ?? base.cardTheme.shape,
        shadowColor: cardShadowColor ?? base.cardTheme.shadowColor,
        elevation: (cardShadowColor != null) ? 1 : base.cardTheme.elevation,
      ),
      dialogTheme: base.dialogTheme.copyWith(
        shape: cardShape ?? base.dialogTheme.shape,
      ),
      inputDecorationTheme: base.inputDecorationTheme.copyWith(
        border: inputBorder ?? base.inputDecorationTheme.border,
        enabledBorder: inputBorder ?? base.inputDecorationTheme.enabledBorder,
        focusedBorder: inputFocusedBorder ?? base.inputDecorationTheme.focusedBorder,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: (base.filledButtonTheme.style ?? const ButtonStyle()).copyWith(
          shape: buttonShape != null ? WidgetStatePropertyAll(buttonShape) : null,
          textStyle: WidgetStatePropertyAll(
            TextStyle(
              fontFamily: (fontFamily != null && fontFamily.isNotEmpty) ? fontFamily : null,
              fontWeight: boldW,
            ),
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: (base.outlinedButtonTheme.style ?? const ButtonStyle()).copyWith(
          shape: buttonShape != null ? WidgetStatePropertyAll(buttonShape) : null,
          textStyle: WidgetStatePropertyAll(
            TextStyle(
              fontFamily: (fontFamily != null && fontFamily.isNotEmpty) ? fontFamily : null,
              fontWeight: boldW,
            ),
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: (base.textButtonTheme.style ?? const ButtonStyle()).copyWith(
          shape: buttonShape != null ? WidgetStatePropertyAll(buttonShape) : null,
          textStyle: WidgetStatePropertyAll(
            TextStyle(
              fontFamily: (fontFamily != null && fontFamily.isNotEmpty) ? fontFamily : null,
              fontWeight: boldW,
            ),
          ),
        ),
      ),
    );
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

  static Map<String, dynamic> _asMap(dynamic raw) {
    if (raw is Map<String, dynamic>) return raw;
    if (raw is Map) return Map<String, dynamic>.from(raw);
    return const <String, dynamic>{};
  }

  static double? _tryParseDouble(dynamic raw) {
    if (raw == null) return null;
    if (raw is num) return raw.toDouble();
    if (raw is String) return double.tryParse(raw.trim());
    return null;
  }

  static FontWeight? _tryParseFontWeight(dynamic raw) {
    final v = _tryParseDouble(raw);
    if (v == null) return null;

    final rounded = v.round();
    switch (rounded) {
      case 100:
        return FontWeight.w100;
      case 200:
        return FontWeight.w200;
      case 300:
        return FontWeight.w300;
      case 400:
        return FontWeight.w400;
      case 500:
        return FontWeight.w500;
      case 600:
        return FontWeight.w600;
      case 700:
        return FontWeight.w700;
      case 800:
        return FontWeight.w800;
      case 900:
        return FontWeight.w900;
      default:
        return null;
    }
  }
}
