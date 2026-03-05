import { api } from './http'
import type { CharacterCreate, CharacterOut, CharacterUpdate } from '../types/characters'

export async function listPublicCharacters(p?: { skip?: number; limit?: number; nsfw?: boolean | null }) {
  const resp = await api.get<CharacterOut[]>('/characters/public', {
    params: {
      skip: p?.skip ?? 0,
      limit: p?.limit ?? 50,
      nsfw: typeof p?.nsfw === 'boolean' ? p.nsfw : undefined,
    },
  })
  return resp.data
}

export async function getPublicCharacter(p: { characterId: string }) {
  const resp = await api.get<CharacterOut>(`/characters/public/${p.characterId}`)
  return resp.data
}

export async function listMyCharacters(p?: { skip?: number; limit?: number }) {
  const resp = await api.get<CharacterOut[]>('/characters/me', {
    params: {
      skip: p?.skip ?? 0,
      limit: p?.limit ?? 50,
    },
  })
  return resp.data
}

export async function createCharacter(body: CharacterCreate) {
  const resp = await api.post<CharacterOut>('/characters/me', body)
  return resp.data
}

export async function updateCharacter(p: { characterId: string; body: CharacterUpdate }) {
  const resp = await api.patch<CharacterOut>(`/characters/me/${p.characterId}`, p.body)
  return resp.data
}

export async function deleteCharacter(p: { characterId: string }) {
  await api.delete(`/characters/me/${p.characterId}`)
}
