import { create } from 'zustand'

type AuthState = {
  accessToken: string | null
  refreshToken: string | null
  sessionId: string | null
  deviceId: string | null
  setTokens: (p: { accessToken: string; refreshToken: string | null; sessionId: string | null }) => void
  setDeviceId: (deviceId: string) => void
  logout: () => void
}

const LS_KEY = 'ng_auth_v1'

function safeParse(json: string | null): any {
  if (!json) return null
  try {
    return JSON.parse(json)
  } catch {
    return null
  }
}

const initial = (() => {
  const raw = safeParse(localStorage.getItem(LS_KEY))
  return {
    accessToken: typeof raw?.accessToken === 'string' ? raw.accessToken : null,
    refreshToken: typeof raw?.refreshToken === 'string' ? raw.refreshToken : null,
    sessionId: typeof raw?.sessionId === 'string' ? raw.sessionId : null,
    deviceId: typeof raw?.deviceId === 'string' ? raw.deviceId : null,
  }
})()

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: initial.accessToken,
  refreshToken: initial.refreshToken,
  sessionId: initial.sessionId,
  deviceId: initial.deviceId,
  setTokens: ({ accessToken, refreshToken, sessionId }) => {
    const next = {
      ...get(),
      accessToken,
      refreshToken,
      sessionId,
    }
    localStorage.setItem(
      LS_KEY,
      JSON.stringify({
        accessToken: next.accessToken,
        refreshToken: next.refreshToken,
        sessionId: next.sessionId,
        deviceId: next.deviceId,
      }),
    )
    set({ accessToken, refreshToken, sessionId })
  },
  setDeviceId: (deviceId) => {
    const next = { ...get(), deviceId }
    localStorage.setItem(
      LS_KEY,
      JSON.stringify({
        accessToken: next.accessToken,
        refreshToken: next.refreshToken,
        sessionId: next.sessionId,
        deviceId: next.deviceId,
      }),
    )
    set({ deviceId })
  },
  logout: () => {
    localStorage.removeItem(LS_KEY)
    set({ accessToken: null, refreshToken: null, sessionId: null })
  },
}))
