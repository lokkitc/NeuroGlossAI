import 'package:equatable/equatable.dart';

class ThemeTokensEntity extends Equatable {
  const ThemeTokensEntity({
    required this.version,
    required this.schema,
    required this.palette,
    this.typography,
    this.components,
    this.effects,
    this.extensions,
  });

  final int version;
  final String schema;
  final Map<String, dynamic> palette;
  final Map<String, dynamic>? typography;
  final Map<String, dynamic>? components;
  final Map<String, dynamic>? effects;
  final Map<String, dynamic>? extensions;

  @override
  List<Object?> get props => [version, schema, palette, typography, components, effects, extensions];
}

class AppThemeEntity extends Equatable {
  const AppThemeEntity({
    required this.id,
    required this.themeType,
    required this.slug,
    required this.displayName,
    required this.description,
    required this.isPublic,
    this.ownerUserId,
    this.lightTokens,
    this.darkTokens,
  });

  final String id;
  final String themeType;
  final String slug;
  final String displayName;
  final String description;
  final bool isPublic;
  final String? ownerUserId;

  final ThemeTokensEntity? lightTokens;
  final ThemeTokensEntity? darkTokens;

  @override
  List<Object?> get props => [
        id,
        themeType,
        slug,
        displayName,
        description,
        isPublic,
        ownerUserId,
        lightTokens,
        darkTokens,
      ];
}
