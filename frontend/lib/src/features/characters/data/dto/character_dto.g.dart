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
      avatarUrl: json['avatar_url'] as String?,
      thumbnailUrl: json['thumbnail_url'] as String?,
      bannerUrl: json['banner_url'] as String?,
      greeting: json['greeting'] as String?,
      tags: (json['tags'] as List<dynamic>?)?.map((e) => e.toString()).toList(),
      voiceProvider: json['voice_provider'] as String?,
      voiceId: json['voice_id'] as String?,
      voiceSettings: json['voice_settings'] as Map<String, dynamic>?,
      chatSettings: json['chat_settings'] as Map<String, dynamic>?,
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
      'avatar_url': instance.avatarUrl,
      'thumbnail_url': instance.thumbnailUrl,
      'banner_url': instance.bannerUrl,
      'greeting': instance.greeting,
      'tags': instance.tags,
      'voice_provider': instance.voiceProvider,
      'voice_id': instance.voiceId,
      'voice_settings': instance.voiceSettings,
      'chat_settings': instance.chatSettings,
      'is_public': instance.isPublic,
      'is_nsfw': instance.isNsfw,
      'settings': instance.settings,
    };
