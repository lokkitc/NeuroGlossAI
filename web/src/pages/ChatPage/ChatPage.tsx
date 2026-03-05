import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { NavLink, useNavigate, useParams } from 'react-router-dom'
import * as chat from '../../services/chat'
import * as characters from '../../services/characters'
import Card from '../../components/ui/Card/Card'
import Button from '../../components/ui/Button/Button'
import LoadingState from '../../components/states/LoadingState/LoadingState'
import ErrorState from '../../components/states/ErrorState/ErrorState'
import EmptyState from '../../components/states/EmptyState/EmptyState'
import styles from './ChatPage.module.css'

export default function ChatPage() {
  const params = useParams() as { sessionId?: string }
  const nav = useNavigate()
  const qc = useQueryClient()

  const sessionsQ = useQuery({
    queryKey: ['chat', 'sessions'],
    queryFn: () => chat.listSessions({ skip: 0, limit: 100 }),
  })

  const selectedSessionId = params.sessionId || sessionsQ.data?.[0]?.id || null

  const sessionQ = useQuery({
    queryKey: ['chat', 'session', selectedSessionId],
    queryFn: () => chat.getSession({ sessionId: selectedSessionId as string }),
    enabled: Boolean(selectedSessionId),
  })

  const publicCharactersQ = useQuery({
    queryKey: ['characters', 'public', 'forNewSession'],
    queryFn: () => characters.listPublicCharacters({ skip: 0, limit: 60 }),
  })

  const [newMessage, setNewMessage] = useState('')
  const [newSessionCharacterId, setNewSessionCharacterId] = useState<string>('')

  useEffect(() => {
    if (!newSessionCharacterId && publicCharactersQ.data && publicCharactersQ.data.length > 0) {
      setNewSessionCharacterId(publicCharactersQ.data[0].id)
    }
  }, [publicCharactersQ.data, newSessionCharacterId])

  const createSessionM = useMutation({
    mutationFn: async () => {
      if (!newSessionCharacterId) {
        throw new Error('Pick a character')
      }
      return chat.createSession({ title: '', character_id: newSessionCharacterId, room_id: null })
    },
    onSuccess: async (sess) => {
      await qc.invalidateQueries({ queryKey: ['chat', 'sessions'] })
      nav(`/chat/${sess.id}`)
    },
  })

  const sendM = useMutation({
    mutationFn: async () => {
      const sid = selectedSessionId
      if (!sid) throw new Error('No session')
      const content = newMessage.trim()
      if (!content) throw new Error('Type a message')
      setNewMessage('')
      return chat.createTurn({ sessionId: sid, content })
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['chat', 'session', selectedSessionId] })
    },
  })

  const thread = useMemo(() => {
    const turns = sessionQ.data?.turns || []
    return turns
  }, [sessionQ.data])

  return (
    <div className={styles.root}>
      <div className={styles.left}>
        <div className={styles.leftHeader}>
          <div className={styles.leftTitle}>Sessions</div>
        </div>

        <Card className={styles.newSessionCard}>
          <div className={styles.newSessionTop}>New session</div>
          {publicCharactersQ.isLoading ? <LoadingState lines={2} /> : null}
          {publicCharactersQ.isError ? (
            <ErrorState message={(publicCharactersQ.error as any)?.message || 'Failed to load characters'} />
          ) : null}
          {publicCharactersQ.isSuccess ? (
            <select
              className={styles.select}
              value={newSessionCharacterId}
              onChange={(e) => setNewSessionCharacterId(e.target.value)}
            >
              {publicCharactersQ.data.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.display_name} (@{c.slug})
                </option>
              ))}
            </select>
          ) : null}
          <div className={styles.newSessionActions}>
            <Button disabled={createSessionM.isPending} onClick={() => createSessionM.mutate()}>
              {createSessionM.isPending ? 'Creating…' : 'Create'}
            </Button>
          </div>
          {createSessionM.isError ? (
            <div className={styles.errorText}>{(createSessionM.error as any)?.message || 'Failed'}</div>
          ) : null}
        </Card>

        {sessionsQ.isLoading ? <LoadingState lines={6} /> : null}
        {sessionsQ.isError ? (
          <ErrorState message={(sessionsQ.error as any)?.message || 'Failed to load sessions'} onRetry={() => sessionsQ.refetch()} />
        ) : null}
        {sessionsQ.isSuccess && sessionsQ.data.length === 0 ? (
          <EmptyState title='No sessions' message='Create a new session to start chatting.' />
        ) : null}
        {sessionsQ.isSuccess && sessionsQ.data.length > 0 ? (
          <div className={styles.sessionList}>
            {sessionsQ.data.map((s) => (
              <NavLink
                key={s.id}
                to={`/chat/${s.id}`}
                className={({ isActive }) => (isActive ? styles.sessionActive : styles.sessionLink)}
              >
                <div className={styles.sessionTitle}>{s.title || 'Untitled'}</div>
                <div className={styles.sessionMeta}>{s.character_id ? 'character' : 'room'}</div>
              </NavLink>
            ))}
          </div>
        ) : null}
      </div>

      <div className={styles.right}>
        <div className={styles.threadHeader}>
          <div className={styles.threadTitle}>Chat</div>
          {selectedSessionId ? <div className={styles.threadId}>{selectedSessionId}</div> : null}
        </div>

        {!selectedSessionId ? <EmptyState title='Pick or create a session' /> : null}
        {selectedSessionId && sessionQ.isLoading ? <LoadingState lines={10} /> : null}
        {selectedSessionId && sessionQ.isError ? (
          <ErrorState message={(sessionQ.error as any)?.message || 'Failed to load session'} onRetry={() => sessionQ.refetch()} />
        ) : null}

        {selectedSessionId && sessionQ.isSuccess ? (
          <Card className={styles.threadCard}>
            <div className={styles.turns}>
              {thread.length === 0 ? (
                <div className={styles.emptyThread}>Say hi to start the conversation.</div>
              ) : (
                thread.map((t) => (
                  <div
                    key={t.id}
                    className={
                      (t.meta?.kind === 'action'
                        ? t.role === 'user'
                          ? styles.turnUserAction
                          : styles.turnAssistantAction
                        : t.role === 'user'
                          ? styles.turnUser
                          : styles.turnAssistant) as string
                    }
                  >
                    {t.meta?.kind !== 'action' ? <div className={styles.turnRole}>{t.role}</div> : null}
                    <div className={styles.turnContent}>{t.content}</div>
                  </div>
                ))
              )}
            </div>

            <form
              className={styles.composer}
              onSubmit={(e) => {
                e.preventDefault()
                sendM.mutate()
              }}
            >
              <textarea
                className={styles.textarea}
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder='Write a message…'
                rows={3}
              />
              <div className={styles.composerActions}>
                <Button type='submit' disabled={sendM.isPending}>
                  {sendM.isPending ? 'Sending…' : 'Send'}
                </Button>
              </div>
              {sendM.isError ? (
                <div className={styles.errorText}>{(sendM.error as any)?.message || 'Failed to send'}</div>
              ) : null}
            </form>
          </Card>
        ) : null}
      </div>
    </div>
  )
}
