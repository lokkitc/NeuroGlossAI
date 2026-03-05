import { api } from './http'
import type {
  ChatSessionCreate,
  ChatSessionDetail,
  ChatSessionOut,
  ChatTurnResponse,
} from '../types/chat'

export async function listSessions(p?: { skip?: number; limit?: number }) {
  const resp = await api.get<ChatSessionOut[]>('/chat/sessions', {
    params: {
      skip: p?.skip ?? 0,
      limit: p?.limit ?? 50,
    },
  })
  return resp.data
}

export async function createSession(body: ChatSessionCreate) {
  const resp = await api.post<ChatSessionOut>('/chat/sessions', {
    title: body.title ?? '',
    character_id: body.character_id ?? null,
    room_id: body.room_id ?? null,
  })
  return resp.data
}

export async function getSession(p: { sessionId: string }) {
  const resp = await api.get<ChatSessionDetail>(`/chat/sessions/${p.sessionId}`)
  return resp.data
}

export async function createTurn(p: { sessionId: string; content: string }) {
  const resp = await api.post<ChatTurnResponse>(`/chat/sessions/${p.sessionId}/turn`, {
    content: p.content,
  })
  return resp.data
}
