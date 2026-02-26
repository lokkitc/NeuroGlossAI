from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import Any, Literal

from app.features.themes.enums import ThemeType


class PaletteTokens(BaseModel):
    primary: str
    secondary: str
    background: str
    surface: str
    error: str
    success: str
    warning: str
    info: str
    textPrimary: str
    textSecondary: str
    border: str
    divider: str
    hover: str
    active: str
    disabled: str

    model_config = {"extra": "allow"}


class TypographyTokens(BaseModel):
    fontFamily: str | None = None
    fontWeights: dict[str, int] = Field(default_factory=dict)
    fontSizes: dict[str, float] = Field(default_factory=dict)
    lineHeights: dict[str, float] = Field(default_factory=dict)
    letterSpacing: dict[str, float] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class MotionTokens(BaseModel):
    durationMs: dict[str, int] = Field(default_factory=dict)
    easing: dict[str, str] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class EffectsTokens(BaseModel):
    gradients: dict[str, Any] = Field(default_factory=dict)
    shadows: dict[str, Any] = Field(default_factory=dict)
    borderRadius: dict[str, float] = Field(default_factory=dict)  # sm,md,lg,xl
    spacing: dict[str, float] = Field(default_factory=dict)
    motion: MotionTokens = Field(default_factory=MotionTokens)

    model_config = {"extra": "allow"}


class ComponentTokens(BaseModel):
    button: dict[str, Any] = Field(default_factory=dict)
    card: dict[str, Any] = Field(default_factory=dict)
    input: dict[str, Any] = Field(default_factory=dict)
    appBar: dict[str, Any] = Field(default_factory=dict)
    drawer: dict[str, Any] = Field(default_factory=dict)
    badge: dict[str, Any] = Field(default_factory=dict)
    chip: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class ThemeTokens(BaseModel):
    version: int = 1
    schema: Literal["neurogloss.v1"] = "neurogloss.v1"

    palette: PaletteTokens
    typography: TypographyTokens = Field(default_factory=TypographyTokens)
    components: ComponentTokens = Field(default_factory=ComponentTokens)
    effects: EffectsTokens = Field(default_factory=EffectsTokens)

    extensions: dict[str, Any] = Field(default_factory=dict)


class ThemeBase(BaseModel):
    theme_type: ThemeType
    slug: str
    display_name: str
    description: str = ""
    is_public: bool = False

    light_tokens: ThemeTokens | None = None
    dark_tokens: ThemeTokens | None = None

    @field_validator("slug")
    @classmethod
    def _slug(cls, v: str):
        v = (v or "").strip()
        if not v:
            raise ValueError("slug is required")
        if len(v) > 64:
            raise ValueError("slug too long")
        return v


class ThemeCreate(ThemeBase):
    pass


class ThemeUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    is_public: bool | None = None
    light_tokens: ThemeTokens | None = None
    dark_tokens: ThemeTokens | None = None


class ThemeOut(ThemeBase):
    id: UUID
    owner_user_id: UUID | None = None

    class Config:
        from_attributes = True


class SelectThemeRequest(BaseModel):
    theme_id: UUID
