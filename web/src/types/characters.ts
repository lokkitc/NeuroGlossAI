export type CharacterBase = {
  slug: string
  display_name: string
  description: string
  system_prompt: string
  style_prompt?: string | null

  avatar_url?: string | null
  thumbnail_url?: string | null
  banner_url?: string | null

  greeting?: string | null

  tags?: string[] | null

  voice_provider?: string | null
  voice_id?: string | null
  voice_settings?: Record<string, any> | null

  chat_settings?: Record<string, any> | null

  chat_theme_id?: string | null

  is_public: boolean
  is_nsfw: boolean
  settings?: Record<string, any> | null
}

export type CharacterCreate = CharacterBase

export type CharacterUpdate = Partial<
  Pick<
    CharacterBase,
    | 'display_name'
    | 'description'
    | 'system_prompt'
    | 'style_prompt'
    | 'avatar_url'
    | 'thumbnail_url'
    | 'banner_url'
    | 'greeting'
    | 'tags'
    | 'voice_provider'
    | 'voice_id'
    | 'voice_settings'
    | 'chat_settings'
    | 'is_public'
    | 'is_nsfw'
    | 'settings'
  >
>

export type CharacterOut = CharacterBase & {
  id: string
  owner_user_id: string
}
