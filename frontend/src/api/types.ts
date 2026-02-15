export type ApiErrorPayload = {
  code?: string
  message?: string
  detail?: unknown
  request_id?: string
}

export class ApiError extends Error {
  public readonly status: number
  public readonly code?: string
  public readonly requestId?: string

  constructor(params: { status: number; message: string; code?: string; requestId?: string }) {
    super(params.message)
    this.name = 'ApiError'
    this.status = params.status
    this.code = params.code
    this.requestId = params.requestId
  }
}
