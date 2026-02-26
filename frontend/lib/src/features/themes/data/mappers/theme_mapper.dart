import '../../domain/entities/app_theme_entity.dart';
import '../dto/app_theme_dto.dart';

class ThemeMapper {
  static ThemeTokensEntity _toTokens(ThemeTokensDto dto) {
    return ThemeTokensEntity(
      version: dto.version,
      schema: dto.schema,
      palette: dto.palette,
      typography: dto.typography,
      components: dto.components,
      effects: dto.effects,
      extensions: dto.extensions,
    );
  }

  static AppThemeEntity toEntity(AppThemeDto dto) {
    return AppThemeEntity(
      id: dto.id,
      themeType: dto.themeType,
      slug: dto.slug,
      displayName: dto.displayName,
      description: dto.description ?? '',
      isPublic: dto.isPublic ?? false,
      ownerUserId: dto.ownerUserId,
      lightTokens: dto.lightTokens == null ? null : _toTokens(dto.lightTokens!),
      darkTokens: dto.darkTokens == null ? null : _toTokens(dto.darkTokens!),
    );
  }
}
