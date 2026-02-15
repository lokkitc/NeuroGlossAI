import { apiRequest, apiRequestForm } from './apiClient'

export type TokenResponse = { access_token: string; token_type: string }

export type MeResponse = {
  id: string
  email: string
  username: string
  xp: number
  language_levels: Record<string, string>
  target_language: string
  native_language: string
  interests: string[]
}

export const authApi = {
  register: (body: { email: string; username: string; password: string }) =>
    apiRequest<MeResponse>({ path: '/auth/register', method: 'POST', body, auth: false }),
  login: (form: { username: string; password: string }) =>
    apiRequestForm<TokenResponse>({
      path: '/auth/login',
      method: 'POST',
      form,
      auth: false,
    }),
  me: () => apiRequest<MeResponse>({ path: '/auth/me', method: 'GET' }),
}
