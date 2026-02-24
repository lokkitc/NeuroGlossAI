// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'character_dto.dart';

// ***************************************************************************
// JsonSerializableGenerator
// ***************************************************************************

CharacterDto _$CharacterDtoFromJson(Map<String, dynamic> json) => CharacterDto(
      id: json['id'] as String,
      ownerUserId: json['owner_user_id'] as String,
      slug: json['slug'] as String,
      displayName: json['display_name'] as String,
      description: json['description'] as String,
      systemPrompt: json['system_prompt'] as String,
      stylePrompt: json['style_prompt'] as String?,
      isPublic: json['is_public'] as bool,
      isNsfw: json['is_nsfw'] as bool,
      settings: json['settings'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$CharacterDtoToJson(CharacterDto instance) => <String, dynamic>{
      'id': instance.id,
      'owner_user_id': instance.ownerUserId,
      'slug': instance.slug,
      'display_name': instance.displayName,
      'description': instance.description,
      'system_prompt': instance.systemPrompt,
      'style_prompt': instance.stylePrompt,
      'is_public': instance.isPublic,
      'is_nsfw': instance.isNsfw,
      'settings': instance.settings,
    };
