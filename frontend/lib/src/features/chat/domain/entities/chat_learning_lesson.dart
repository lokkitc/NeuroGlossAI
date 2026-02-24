import 'package:equatable/equatable.dart';

class ChatLearningLessonEntity extends Equatable {
  const ChatLearningLessonEntity({
    required this.id,
    required this.ownerUserId,
    required this.chatSessionId,
    required this.sourceTurnFrom,
    required this.sourceTurnTo,
    required this.title,
    required this.topicSnapshot,
    required this.contentText,
    required this.vocabulary,
    required this.exercises,
    required this.provider,
    required this.model,
    required this.qualityStatus,
    required this.createdAt,
  });

  final String id;
  final String ownerUserId;
  final String chatSessionId;
  final int sourceTurnFrom;
  final int sourceTurnTo;
  final String title;
  final String? topicSnapshot;
  final String contentText;
  final Object? vocabulary;
  final Object? exercises;
  final String? provider;
  final String? model;
  final String? qualityStatus;
  final DateTime? createdAt;

  @override
  List<Object?> get props => [
        id,
        ownerUserId,
        chatSessionId,
        sourceTurnFrom,
        sourceTurnTo,
        title,
        topicSnapshot,
        contentText,
        vocabulary,
        exercises,
        provider,
        model,
        qualityStatus,
        createdAt,
      ];
}
