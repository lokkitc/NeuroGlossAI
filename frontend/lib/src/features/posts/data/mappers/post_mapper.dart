import '../../domain/entities/post.dart';

class PostMapper {
  static PostEntity fromJson(Map<String, dynamic> json) {
    final mediaRaw = json['media'];
    final media = <PostMediaEntity>[];
    if (mediaRaw is List) {
      for (final it in mediaRaw) {
        if (it is Map) {
          final m = Map<String, dynamic>.from(it);
          final url = (m['url'] ?? '').toString();
          if (url.isEmpty) continue;
          media.add(
            PostMediaEntity(
              url: url,
              publicId: m['public_id']?.toString(),
              width: _toInt(m['width']),
              height: _toInt(m['height']),
              bytes: _toInt(m['bytes']),
              format: m['format']?.toString(),
            ),
          );
        }
      }
    }

    return PostEntity(
      id: (json['id'] ?? '').toString(),
      authorUserId: (json['author_user_id'] ?? '').toString(),
      authorUsername: json['author_username']?.toString(),
      authorAvatarUrl: json['author_avatar_url']?.toString(),
      characterId: json['character_id']?.toString(),
      characterDisplayName: json['character_display_name']?.toString(),
      characterAvatarUrl: json['character_avatar_url']?.toString(),
      title: (json['title'] ?? '').toString(),
      content: (json['content'] ?? '').toString(),
      media: media,
      isPublic: json['is_public'] == true,
      createdAt: _toDateTime(json['created_at']),
    );
  }

  static int? _toInt(Object? v) {
    if (v is int) return v;
    return int.tryParse('$v');
  }

  static DateTime? _toDateTime(Object? v) {
    if (v == null) return null;
    if (v is String) {
      return DateTime.tryParse(v);
    }
    return null;
  }

  static Map<String, dynamic> mediaToJson(PostMediaEntity m) {
    return {
      'url': m.url,
      'public_id': m.publicId,
      'width': m.width,
      'height': m.height,
      'bytes': m.bytes,
      'format': m.format,
    };
  }
}
