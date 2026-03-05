export type ChatSessionCreate = {
  title?: string
  character_id?: string | null
  room_id?: string | null
}

export type ChatTurnCreate = {
  content: string
}

export type ChatTurnOut = {
  id: string
  session_id: string
  turn_index: number
  role: string
  character_id?: string | null
  content: string
  meta?: Record<string, any> | null
}

export type ChatSessionOut = {
  id: string
  owner_user_id: string
  character_id?: string | null
  room_id?: string | null
  title: string
  is_archived: boolean
}

export type ChatSessionDetail = ChatSessionOut & {
  turns: ChatTurnOut[]
}

export type ChatTurnResponse = {
  session: ChatSessionOut
  user_turn: ChatTurnOut
  assistant_turns: ChatTurnOut[]
  memory_used: Array<Record<string, any>>
}
