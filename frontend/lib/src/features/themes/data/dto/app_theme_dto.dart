import 'package:json_annotation/json_annotation.dart';

part 'app_theme_dto.g.dart';

@JsonSerializable()
class ThemeTokensDto {
  const ThemeTokensDto({
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

  factory ThemeTokensDto.fromJson(Map<String, dynamic> json) => _$ThemeTokensDtoFromJson(json);
  Map<String, dynamic> toJson() => _$ThemeTokensDtoToJson(this);
}

@JsonSerializable()
class AppThemeDto {
  const AppThemeDto({
    required this.id,
    required this.themeType,
    required this.slug,
    required this.displayName,
    this.description,
    this.isPublic,
    this.ownerUserId,
    this.lightTokens,
    this.darkTokens,
  });

  final String id;

  @JsonKey(name: 'theme_type')
  final String themeType;

  final String slug;

  @JsonKey(name: 'display_name')
  final String displayName;

  final String? description;

  @JsonKey(name: 'is_public')
  final bool? isPublic;

  @JsonKey(name: 'owner_user_id')
  final String? ownerUserId;

  @JsonKey(name: 'light_tokens')
  final ThemeTokensDto? lightTokens;

  @JsonKey(name: 'dark_tokens')
  final ThemeTokensDto? darkTokens;

  factory AppThemeDto.fromJson(Map<String, dynamic> json) => _$AppThemeDtoFromJson(json);
  Map<String, dynamic> toJson() => _$AppThemeDtoToJson(this);
}
