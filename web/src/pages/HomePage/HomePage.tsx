import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import styles from './HomePage.module.css'
import * as characters from '../../services/characters'
import * as chat from '../../services/chat'
import type { CharacterOut } from '../../types/characters'
import Card from '../../components/ui/Card/Card'
import Button from '../../components/ui/Button/Button'
import ErrorState from '../../components/states/ErrorState/ErrorState'
import LoadingState from '../../components/states/LoadingState/LoadingState'
import EmptyState from '../../components/states/EmptyState/EmptyState'

function CharacterCard({ c, onStartChat }: { c: CharacterOut; onStartChat: () => void }) {
  const nav = useNavigate()
  return (
    <Card className={styles.characterCard}>
      <button className={styles.characterClickArea} onClick={() => nav(`/characters/${c.id}`)}>
      <div className={styles.characterTop}>
        <div className={styles.characterName}>{c.display_name}</div>
        <div className={styles.characterSlug}>@{c.slug}</div>
      </div>
      <div className={styles.characterDesc}>{c.description || 'No description'}</div>
      <div className={styles.characterMeta}>
        <span className={styles.badge}>{c.is_public ? 'public' : 'private'}</span>
        <span className={styles.badge}>{c.is_nsfw ? 'nsfw' : 'sfw'}</span>
      </div>
      </button>
      <div className={styles.characterActions}>
        <Button onClick={onStartChat}>Chat</Button>
      </div>
    </Card>
  )
}

export default function HomePage() {
  const nav = useNavigate()

  const q = useQuery({
    queryKey: ['characters', 'public'],
    queryFn: () => characters.listPublicCharacters({ skip: 0, limit: 60 }),
  })

  async function startChatWithCharacter(characterId: string) {
    const sess = await chat.createSession({ title: '', character_id: characterId, room_id: null })
    nav(`/chat/${sess.id}`)
  }

  return (
    <div className={styles.root}>
      <div className={styles.hero}>
        <h1 className={styles.title}>Discover characters</h1>
        <p className={styles.subtitle}>Pick a character and start a chat. Auth is required to chat.</p>
      </div>

      {q.isLoading ? <LoadingState lines={6} /> : null}
      {q.isError ? (
        <ErrorState message={(q.error as any)?.message || 'Failed to load characters'} onRetry={() => q.refetch()} />
      ) : null}
      {q.isSuccess && q.data.length === 0 ? (
        <EmptyState title='No characters yet' message='Create one in “Create” after logging in.' />
      ) : null}

      {q.isSuccess && q.data.length > 0 ? (
        <div className={styles.grid}>
          {q.data.map((c) => (
            <CharacterCard key={c.id} c={c} onStartChat={() => startChatWithCharacter(c.id)} />
          ))}
        </div>
      ) : null}
    </div>
  )
}
