import 'package:equatable/equatable.dart';

class ChatTurnEntity extends Equatable {
  const ChatTurnEntity({
    required this.id,
    required this.sessionId,
    required this.turnIndex,
    required this.role,
    required this.content,
    this.characterId,
    this.meta,
  });

  final String id;
  final String sessionId;
  final int turnIndex;
  final String role;
  final String content;
  final String? characterId;
  final Map<String, dynamic>? meta;

  bool get isUser => role == 'user';

  @override
  List<Object?> get props => [id, sessionId, turnIndex, role, content, characterId, meta];
}
