import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import styles from './CharacterDetailPage.module.css'
import * as characters from '../../services/characters'
import * as chat from '../../services/chat'
import { useAuthStore } from '../../store/authStore'
import Card from '../../components/ui/Card/Card'
import Button from '../../components/ui/Button/Button'
import ErrorState from '../../components/states/ErrorState/ErrorState'
import LoadingState from '../../components/states/LoadingState/LoadingState'

export default function CharacterDetailPage() {
  const { characterId } = useParams()
  const nav = useNavigate()
  const isAuthed = useAuthStore((s) => Boolean(s.accessToken))

  const id = useMemo(() => (characterId || '').trim(), [characterId])

  const q = useQuery({
    queryKey: ['characters', 'public', 'detail', id],
    queryFn: () => characters.getPublicCharacter({ characterId: id }),
    enabled: Boolean(id),
  })

  async function startChat() {
    if (!q.data) return
    if (!isAuthed) {
      nav('/login')
      return
    }
    const sess = await chat.createSession({ title: '', character_id: q.data.id, room_id: null })
    nav(`/chat/${sess.id}`)
  }

  if (!id) {
    return <ErrorState message='Missing character id' />
  }

  if (q.isLoading) {
    return <LoadingState lines={6} />
  }

  if (q.isError) {
    return <ErrorState message={(q.error as any)?.message || 'Failed to load character'} onRetry={() => q.refetch()} />
  }

  if (!q.data) {
    return <ErrorState message='Character not found' />
  }

  const c = q.data

  return (
    <div className={styles.root}>
      <div className={styles.top}>
        <div className={styles.avatarWrap}>
          {c.avatar_url ? <img className={styles.avatarImg} src={c.avatar_url} alt={c.display_name} /> : null}
          {!c.avatar_url ? <div className={styles.avatarFallback}>{c.display_name.slice(0, 1).toUpperCase()}</div> : null}
        </div>

        <div className={styles.headerText}>
          <div className={styles.nameRow}>
            <div className={styles.name}>{c.display_name}</div>
            <div className={styles.slug}>@{c.slug}</div>
          </div>
          <div className={styles.desc}>{c.description || 'No description'}</div>

          <div className={styles.metaRow}>
            <span className={styles.pill}>{c.is_public ? 'public' : 'private'}</span>
            <span className={styles.pill}>{c.is_nsfw ? 'nsfw' : 'sfw'}</span>
            {Array.isArray(c.tags) ? c.tags.slice(0, 6).map((t) => <span key={t} className={styles.pill}>{t}</span>) : null}
          </div>

          <div className={styles.actions}>
            <Button onClick={startChat}>{isAuthed ? 'Chat' : 'Login to chat'}</Button>
            <Button variant='ghost' onClick={() => nav(-1)}>
              Back
            </Button>
          </div>
        </div>
      </div>

      {c.greeting ? (
        <Card className={styles.section}>
          <div className={styles.sectionTitle}>Greeting</div>
          <div className={styles.sectionBody}>{c.greeting}</div>
        </Card>
      ) : null}

      <Card className={styles.section}>
        <div className={styles.sectionTitle}>Prompts</div>
        <div className={styles.sectionBody}>
          <div className={styles.kv}>
            <div className={styles.k}>System</div>
            <div className={styles.v}>{c.system_prompt || '—'}</div>
          </div>
          {c.style_prompt ? (
            <div className={styles.kv}>
              <div className={styles.k}>Style</div>
              <div className={styles.v}>{c.style_prompt}</div>
            </div>
          ) : null}
        </div>
      </Card>
    </div>
  )
}
