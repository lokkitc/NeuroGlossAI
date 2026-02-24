import 'package:equatable/equatable.dart';

class CharacterEntity extends Equatable {
  const CharacterEntity({
    required this.id,
    required this.ownerUserId,
    required this.slug,
    required this.displayName,
    required this.description,
    required this.systemPrompt,
    required this.stylePrompt,
    required this.isPublic,
    required this.isNsfw,
    required this.settings,
  });

  final String id;
  final String ownerUserId;
  final String slug;
  final String displayName;
  final String description;
  final String systemPrompt;
  final String? stylePrompt;
  final bool isPublic;
  final bool isNsfw;
  final Map<String, dynamic>? settings;

  @override
  List<Object?> get props => [id, ownerUserId, slug, displayName, description, systemPrompt, stylePrompt, isPublic, isNsfw, settings];
}
