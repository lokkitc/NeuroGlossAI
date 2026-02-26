import 'package:equatable/equatable.dart';

class PostMediaEntity extends Equatable {
  const PostMediaEntity({
    required this.url,
    required this.publicId,
    required this.width,
    required this.height,
    required this.bytes,
    required this.format,
  });

  final String url;
  final String? publicId;
  final int? width;
  final int? height;
  final int? bytes;
  final String? format;

  @override
  List<Object?> get props => [url, publicId, width, height, bytes, format];
}

class PostEntity extends Equatable {
  const PostEntity({
    required this.id,
    required this.authorUserId,
    required this.characterId,
    required this.title,
    required this.content,
    required this.media,
    required this.isPublic,
    required this.createdAt,
  });

  final String id;
  final String authorUserId;
  final String? characterId;
  final String title;
  final String content;
  final List<PostMediaEntity> media;
  final bool isPublic;
  final DateTime? createdAt;

  @override
  List<Object?> get props => [id, authorUserId, characterId, title, content, media, isPublic, createdAt];
}
