// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_theme_dto.dart';

// ***************************************************************************
// JsonSerializableGenerator
// ***************************************************************************

ThemeTokensDto _$ThemeTokensDtoFromJson(Map<String, dynamic> json) => ThemeTokensDto(
      version: (json['version'] as num).toInt(),
      schema: json['schema'] as String,
      palette: Map<String, dynamic>.from(json['palette'] as Map),
      typography: json['typography'] == null ? null : Map<String, dynamic>.from(json['typography'] as Map),
      components: json['components'] == null ? null : Map<String, dynamic>.from(json['components'] as Map),
      effects: json['effects'] == null ? null : Map<String, dynamic>.from(json['effects'] as Map),
      extensions: json['extensions'] == null ? null : Map<String, dynamic>.from(json['extensions'] as Map),
    );

Map<String, dynamic> _$ThemeTokensDtoToJson(ThemeTokensDto instance) => <String, dynamic>{
      'version': instance.version,
      'schema': instance.schema,
      'palette': instance.palette,
      'typography': instance.typography,
      'components': instance.components,
      'effects': instance.effects,
      'extensions': instance.extensions,
    };

AppThemeDto _$AppThemeDtoFromJson(Map<String, dynamic> json) => AppThemeDto(
      id: json['id'] as String,
      themeType: json['theme_type'] as String,
      slug: json['slug'] as String,
      displayName: json['display_name'] as String,
      description: json['description'] as String?,
      isPublic: json['is_public'] as bool?,
      ownerUserId: json['owner_user_id'] as String?,
      lightTokens: json['light_tokens'] == null
          ? null
          : ThemeTokensDto.fromJson(Map<String, dynamic>.from(json['light_tokens'] as Map)),
      darkTokens: json['dark_tokens'] == null
          ? null
          : ThemeTokensDto.fromJson(Map<String, dynamic>.from(json['dark_tokens'] as Map)),
    );

Map<String, dynamic> _$AppThemeDtoToJson(AppThemeDto instance) => <String, dynamic>{
      'id': instance.id,
      'theme_type': instance.themeType,
      'slug': instance.slug,
      'display_name': instance.displayName,
      'description': instance.description,
      'is_public': instance.isPublic,
      'owner_user_id': instance.ownerUserId,
      'light_tokens': instance.lightTokens?.toJson(),
      'dark_tokens': instance.darkTokens?.toJson(),
    };
