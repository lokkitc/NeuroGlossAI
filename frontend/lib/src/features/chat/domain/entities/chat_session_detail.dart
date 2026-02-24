import 'package:equatable/equatable.dart';

import 'chat_session.dart';
import 'chat_turn.dart';

class ChatSessionDetailEntity extends Equatable {
  const ChatSessionDetailEntity({required this.session, required this.turns});

  final ChatSessionEntity session;
  final List<ChatTurnEntity> turns;

  @override
  List<Object?> get props => [session, turns];
}
