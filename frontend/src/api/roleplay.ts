import { apiRequest } from './apiClient'

export type RoleplayMessage = {
  role: 'user' | 'assistant'
  content: string
}

export type RoleplayChatRequest = {
  scenario: string
  role: string
  message: string
  history: Array<Record<string, any>>
  target_language: string
  level: string
}

export type RoleplayChatResponse = { response: string }

export const roleplayApi = {
  chat: (body: RoleplayChatRequest) => apiRequest<RoleplayChatResponse>({ path: '/roleplay/chat', method: 'POST', body }),
}
