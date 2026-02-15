import { create, type StateCreator } from 'zustand'
import { authApi, type MeResponse } from '../api/auth'

const TOKEN_KEY = 'ng_token'

export type AuthState = {
  token: string | null
  me: MeResponse | null
  isLoadingMe: boolean
  setToken: (token: string | null) => void
  logout: () => void
  loadMe: () => Promise<void>
}

function readToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

function writeToken(token: string | null) {
  try {
    if (!token) localStorage.removeItem(TOKEN_KEY)
    else localStorage.setItem(TOKEN_KEY, token)
  } catch {
    // ignore
  }
}

const creator: StateCreator<AuthState> = (set, get) => ({
  token: readToken(),
  me: null,
  isLoadingMe: false,
  setToken: (token: string | null) => {
    writeToken(token)
    set({ token })
  },
  logout: () => {
    writeToken(null)
    set({ token: null, me: null })
  },
  loadMe: async () => {
    const { token } = get()
    if (!token) {
      set({ me: null })
      return
    }

    set({ isLoadingMe: true })
    try {
      const me = await authApi.me()
      set({ me })
    } catch {
      get().logout()
    } finally {
      set({ isLoadingMe: false })
    }
  },
})

export const useAuthStore = create<AuthState>(creator)
