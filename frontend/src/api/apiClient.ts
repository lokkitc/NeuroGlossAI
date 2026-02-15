import { ApiError, type ApiErrorPayload } from './types'

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

function getBaseUrl(): string {
  const url = import.meta.env.VITE_API_BASE_URL as string | undefined
  const effectiveUrl = url && url.trim().length > 0 ? url : 'http://localhost:8000/api/v1'
  return effectiveUrl.replace(/\/$/, '')
}

function readToken(): string | null {
  try {
    return localStorage.getItem('ng_token')
  } catch {
    return null
  }
}

function resolveErrorMessage(payload: ApiErrorPayload | null, fallback: string): string {
  if (!payload) return fallback
  if (payload.message && typeof payload.message === 'string') return payload.message
  if (typeof payload.detail === 'string') return payload.detail
  if (payload.detail && typeof payload.detail === 'object') {
    try {
      return JSON.stringify(payload.detail)
    } catch {
      return fallback
    }
  }
  return fallback
}

async function parseErrorPayload(response: Response): Promise<ApiErrorPayload | null> {
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) return null

  try {
    return (await response.json()) as ApiErrorPayload
  } catch {
    return null
  }
}

export async function apiRequest<T>(params: {
  path: string
  method: HttpMethod
  body?: unknown
  headers?: Record<string, string>
  auth?: boolean
}): Promise<T> {
  const url = `${getBaseUrl()}${params.path.startsWith('/') ? '' : '/'}${params.path}`

  const headers: Record<string, string> = {
    ...(params.headers ?? {}),
  }

  if (params.body !== undefined && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }

  if (params.auth !== false) {
    const token = readToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(url, {
    method: params.method,
    headers,
    body: params.body === undefined ? undefined : JSON.stringify(params.body),
  })

  if (!response.ok) {
    const payload = await parseErrorPayload(response)
    const fallback = response.statusText || `Ошибка запроса (${response.status})`
    const message = resolveErrorMessage(payload, fallback)
    throw new ApiError({
      status: response.status,
      message,
      code: payload?.code,
      requestId: payload?.request_id,
    })
  }

  if (response.status === 204) return undefined as T

  const contentType = response.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) {
    return (await response.json()) as T
  }

  return (await response.text()) as T
}

export async function apiRequestForm<T>(params: {
  path: string
  method: Exclude<HttpMethod, 'GET'>
  form: Record<string, string>
  headers?: Record<string, string>
  auth?: boolean
}): Promise<T> {
  const url = `${getBaseUrl()}${params.path.startsWith('/') ? '' : '/'}${params.path}`

  const headers: Record<string, string> = {
    ...(params.headers ?? {}),
    'Content-Type': 'application/x-www-form-urlencoded',
  }

  if (params.auth !== false) {
    const token = readToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(url, {
    method: params.method,
    headers,
    body: new URLSearchParams(params.form).toString(),
  })

  if (!response.ok) {
    const payload = await parseErrorPayload(response)
    const fallback = response.statusText || `Ошибка запроса (${response.status})`
    const message = resolveErrorMessage(payload, fallback)
    throw new ApiError({
      status: response.status,
      message,
      code: payload?.code,
      requestId: payload?.request_id,
    })
  }

  if (response.status === 204) return undefined as T

  const contentType = response.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) {
    return (await response.json()) as T
  }

  return (await response.text()) as T
}
