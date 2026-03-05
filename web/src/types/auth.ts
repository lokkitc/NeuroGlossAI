export type Token = {
  access_token: string
  token_type: string
  refresh_token?: string | null
  session_id?: string | null
}

export type RefreshTokenRequest = {
  refresh_token: string
}

export type UserResponse = {
  id: string
  username: string
  email: string
  is_admin: boolean

  xp: number
  streak: number
  last_activity_at: any | null
  level: number

  is_active: boolean
  is_verified: boolean
  last_login_at: any | null
  login_count: number

  is_public: boolean
  location: string | null
  social_links: Record<string, any>

  subscription_tier: string
  subscription_expires_at: any | null
  language_levels: Record<string, string>
  target_language: string
  native_language: string
  interests: string[]

  avatar_url: string | null
  thumbnail_url: string | null
  banner_url: string | null
  preferred_name: string | null
  bio: string | null
  timezone: string | null
  ui_theme: string | null
  selected_theme_id: string | null

  assistant_tone: string | null
  assistant_verbosity: number | null
  preferences: Record<string, any>
}
