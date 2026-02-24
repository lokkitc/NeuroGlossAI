import 'package:equatable/equatable.dart';

class ChatSessionEntity extends Equatable {
  const ChatSessionEntity({
    required this.id,
    required this.ownerUserId,
    required this.title,
    required this.isArchived,
    this.characterId,
    this.roomId,
    this.enrollmentId,
    this.activeLevelTemplateId,
  });

  final String id;
  final String ownerUserId;
  final String title;
  final bool isArchived;
  final String? characterId;
  final String? roomId;
  final String? enrollmentId;
  final String? activeLevelTemplateId;

  @override
  List<Object?> get props => [id, ownerUserId, title, isArchived, characterId, roomId, enrollmentId, activeLevelTemplateId];
}
