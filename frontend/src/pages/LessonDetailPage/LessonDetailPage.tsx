import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useLessonById, useRegenCore, useRegenExercises } from '../../api/hooks'
import { Card } from '../../components/ui/Card/Card'
import { Tabs, type TabItem } from '../../components/ui/Tabs/Tabs'
import { EmptyState } from '../../components/states/EmptyState/EmptyState'
import { ErrorState } from '../../components/states/ErrorState/ErrorState'
import { LoadingState } from '../../components/states/LoadingState/LoadingState'
import ExercisePlayer from '../../components/ExercisePlayer/ExercisePlayer'
import { formatDateTime } from '../../utils/format'
import { ui } from '../../styles/ui'
import styles from './LessonDetailPage.module.css'

export function LessonDetailPage() {
  const { id } = useParams()
  const lessonQ = useLessonById(id)
  const regenEx = useRegenExercises()
  const regenCore = useRegenCore()

  const [tab, setTab] = useState('text')

  const canMutate = !regenEx.isPending && !regenCore.isPending

  const items: TabItem[] = useMemo(() => {
    const l = lessonQ.data

    const text = l ? (
      <div className={styles.text}>{l.content_text}</div>
    ) : (
      <EmptyState title="Нет данных" />
    )

    const vocab = l ? (
      l.vocabulary_items.length ? (
        <div className={styles.vocab}>
          {l.vocabulary_items.map((v) => (
            <div key={v.id} className={styles.vocabItem}>
              <div style={ui.text.title}>{v.word ?? '—'}</div>
              <div style={{ color: ui.color.muted, marginTop: ui.space.s2 }}>{v.translation ?? ''}</div>
              {v.context_sentence ? (
                <div style={{ marginTop: ui.space.s3, color: ui.color.text }}>{v.context_sentence}</div>
              ) : null}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="Словарь пуст" description="В этом уроке нет слов для повторения." />
      )
    ) : (
      <EmptyState title="Нет данных" />
    )

    const exercises = l ? (
      l.exercises && l.exercises.length ? (
        <ExercisePlayer exercises={l.exercises} onComplete={(results) => console.log('Exercise results:', results)} />
      ) : (
        <EmptyState title="Упражнения отсутствуют" description="Попробуй регенерацию упражнений." />
      )
    ) : (
      <EmptyState title="Нет данных" />
    )

    return [
      { id: 'text', label: 'Текст', content: text },
      { id: 'vocab', label: 'Словарь', content: vocab },
      { id: 'ex', label: 'Упражнения', content: exercises },
    ]
  }, [lessonQ.data])

  if (lessonQ.isLoading) return <LoadingState title="Загружаю урок…" />
  if (lessonQ.error) return <ErrorState error={lessonQ.error} onRetry={() => lessonQ.refetch()} />
  if (!lessonQ.data) return <EmptyState title="Урок не найден" />

  const lesson = lessonQ.data

  return (
    <Card title="Урок">
      <div className={styles.top}>
        <div>
          <div style={ui.text.title}>{lesson.topic_snapshot || 'Урок'}</div>
          <div style={{ color: ui.color.muted, marginTop: ui.space.s2 }}>
            {formatDateTime(lesson.created_at)} · качество: {lesson.quality_status}
          </div>
          <div style={{ color: ui.color.muted, marginTop: ui.space.s2 }}>
            <Link to="/lessons">← ко всем урокам</Link>
          </div>
        </div>

        <div className={styles.actions}>
          <button
            type="button"
            onClick={() => regenEx.mutate(lesson.id)}
            disabled={!canMutate}
            title="Перегенерировать упражнения"
          >
            {regenEx.isPending ? 'Реген…' : 'Реген упражнений'}
          </button>
          <button
            type="button"
            onClick={() => regenCore.mutate({ id: lesson.id, level: 'A1', generation_mode: 'balanced' })}
            disabled={!canMutate}
            title="Перегенерировать основу"
          >
            {regenCore.isPending ? 'Реген…' : 'Реген основы'}
          </button>
        </div>
      </div>

      {regenEx.error ? <ErrorState error={regenEx.error} title="Ошибка регенерации" /> : null}
      {regenCore.error ? <ErrorState error={regenCore.error} title="Ошибка регенерации" /> : null}

      <div style={ui.mt.s4}>
        <Tabs items={items} value={tab} onChange={setTab} />
      </div>
    </Card>
  )
}
