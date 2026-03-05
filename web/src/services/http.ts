import axios, {
  AxiosError,
  AxiosHeaders,
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios'
import { useAuthStore } from '../store/authStore'
import { getApiBaseUrl, getAppVersion } from './config'
import { ensureDeviceId } from './device'
import type { Token } from '../types/auth'

export type ApiError = {
  status: number
  data: any
  message: string
}

export function isApiError(e: unknown): e is ApiError {
  return Boolean(e) && typeof e === 'object' && 'message' in (e as any) && 'status' in (e as any)
}

export function getErrorMessage(e: unknown, fallback: string) {
  if (isApiError(e)) return e.message || fallback
  if (e && typeof e === 'object' && 'message' in (e as any) && typeof (e as any).message === 'string') {
    return (e as any).message || fallback
  }
  return fallback
}

function toApiError(e: unknown): ApiError {
  if (axios.isAxiosError(e)) {
    const ax = e as AxiosError
    const status = ax.response?.status || 0
    const data = ax.response?.data as any
    const message = (typeof data?.detail === 'string' && data.detail) || ax.message || 'Request failed'
    return { status, data, message }
  }
  return { status: 0, data: null, message: (e as any)?.message || 'Request failed' }
}

let refreshPromise: Promise<Token> | null = null

async function refreshToken(): Promise<Token> {
  const { refreshToken } = useAuthStore.getState()
  if (!refreshToken) {
    throw toApiError({ message: 'No refresh token' })
  }

  const client = axios.create({
    baseURL: getApiBaseUrl(),
    timeout: 60_000,
  })

  const resp = await client.post<Token>('/auth/refresh', {
    refresh_token: refreshToken,
  })

  return resp.data
}

function attachAuthHeaders(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
  const s = useAuthStore.getState()
  const token = s.accessToken
  const sessionId = s.sessionId

  const headers = config.headers instanceof AxiosHeaders ? config.headers : new AxiosHeaders(config.headers)

  headers.set('X-Device-Id', ensureDeviceId())
  headers.set('X-App-Version', getAppVersion())
  if (sessionId) headers.set('X-Session-Id', sessionId)
  if (token) headers.set('Authorization', `Bearer ${token}`)

  config.headers = headers
  return config
}

export function createApiClient(): AxiosInstance {
  const api = axios.create({
    baseURL: getApiBaseUrl(),
    timeout: 60_000,
  })

  api.interceptors.request.use((cfg) => attachAuthHeaders(cfg), (e) => Promise.reject(e))

  api.interceptors.response.use(
    (resp) => resp,
    async (error: AxiosError) => {
      const status = error.response?.status
      const original = error.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined

      if (status !== 401 || !original || original._retry) {
        return Promise.reject(toApiError(error))
      }

      const s = useAuthStore.getState()
      if (!s.refreshToken) {
        s.logout()
        return Promise.reject(toApiError(error))
      }

      try {
        original._retry = true

        if (!refreshPromise) {
          refreshPromise = refreshToken().finally(() => {
            refreshPromise = null
          })
        }

        const t = await refreshPromise
        useAuthStore.getState().setTokens({
          accessToken: t.access_token,
          refreshToken: t.refresh_token ?? null,
          sessionId: t.session_id ?? null,
        })

        const nextCfg = attachAuthHeaders(original as any)
        return api.request(nextCfg)
      } catch (e) {
        useAuthStore.getState().logout()
        return Promise.reject(toApiError(e))
      }
    },
  )

  return api
}

export const api = createApiClient()
