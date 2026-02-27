import 'package:equatable/equatable.dart';

class PublicUserEntity extends Equatable {
  const PublicUserEntity({
    required this.id,
    required this.username,
    this.preferredName,
    this.bio,
    this.selectedThemeId,
    this.avatarUrl,
    this.thumbnailUrl,
    this.bannerUrl,
  });

  final String id;
  final String username;
  final String? preferredName;
  final String? bio;
  final String? selectedThemeId;

  final String? avatarUrl;
  final String? thumbnailUrl;
  final String? bannerUrl;

  @override
  List<Object?> get props => [id, username, preferredName, bio, selectedThemeId, avatarUrl, thumbnailUrl, bannerUrl];
}
