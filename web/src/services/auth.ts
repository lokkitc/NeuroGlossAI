import { api } from './http'
import type { Token, UserResponse } from '../types/auth'
import { useAuthStore } from '../store/authStore'
import { ensureDeviceId } from './device'
import { getAppVersion } from './config'

export async function login(p: { username: string; password: string }): Promise<Token> {
  const body = new URLSearchParams()
  body.set('username', p.username)
  body.set('password', p.password)

  const resp = await api.post<Token>('/auth/login', body, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-Device-Id': ensureDeviceId(),
      'X-App-Version': getAppVersion(),
    },
  })

  const t = resp.data
  useAuthStore.getState().setTokens({
    accessToken: t.access_token,
    refreshToken: t.refresh_token ?? null,
    sessionId: t.session_id ?? null,
  })

  return t
}

export async function register(p: { username: string; email: string; password: string }): Promise<UserResponse> {
  const resp = await api.post<UserResponse>('/auth/register', p)
  return resp.data
}

export async function me(): Promise<UserResponse> {
  const resp = await api.get<UserResponse>('/auth/me')
  return resp.data
}

export async function logout(): Promise<void> {
  const s = useAuthStore.getState()
  const rt = s.refreshToken
  if (!rt) {
    s.logout()
    return
  }
  try {
    await api.post('/auth/logout', { refresh_token: rt })
  } finally {
    s.logout()
  }
}
