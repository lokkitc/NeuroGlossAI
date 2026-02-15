import { apiRequest } from './apiClient'

export type UserResponse = {
  id: string
  username: string
  email: string
  xp: number
  language_levels: Record<string, string>
  target_language: string
  native_language: string
  interests: string[]
}

export type UpdateLanguagesRequest = {
  target_language: string
  native_language: string
}

export type PatchUserRequest = {
  username?: string
  email?: string
  avatar_url?: string
  target_language?: string
  native_language?: string
  interests?: string[]
}

export const usersApi = {
  updateLanguages: (body: UpdateLanguagesRequest) =>
    apiRequest<UserResponse>({ path: '/users/me/languages', method: 'PUT', body }),
  exportMe: () => apiRequest<any>({ path: '/users/me/export', method: 'GET' }),
  resetMe: () => apiRequest<UserResponse>({ path: '/users/me/reset', method: 'POST' }),
  patchMe: (body: PatchUserRequest) => apiRequest<UserResponse>({ path: '/users/me', method: 'PATCH', body }),
}
