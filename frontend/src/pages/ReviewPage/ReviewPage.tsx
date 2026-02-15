import { useMemo, useState } from 'react'
import { useDailyReview, useReviewWord } from '../../api/hooks'
import { Card } from '../../components/ui/Card/Card'
import { EmptyState } from '../../components/states/EmptyState/EmptyState'
import { ErrorState } from '../../components/states/ErrorState/ErrorState'
import { LoadingState } from '../../components/states/LoadingState/LoadingState'
import { clampInt } from '../../utils/format'
import { ui } from '../../styles/ui'
import styles from './ReviewPage.module.css'

export function ReviewPage() {
  const q = useDailyReview()
  const review = useReviewWord()
  const [index, setIndex] = useState(0)

  const items = q.data ?? []
  const current = useMemo(() => items[index] ?? null, [items, index])

  const onRate = async (rating: number) => {
    if (!current) return
    await review.mutateAsync({ vocabulary_id: current.id, rating: clampInt(rating, 1, 5) })
    setIndex((i) => Math.min(i + 1, Math.max(0, items.length - 1)))
  }

  if (q.isLoading) return <LoadingState title="Загружаю слова…" />
  if (q.error) return <ErrorState error={q.error} onRetry={() => q.refetch()} />

  return (
    <div className={styles.wrap}>
      <Card title="Ежедневное повторение">
        {items.length === 0 ? (
          <EmptyState title="На сегодня повторений нет" description="Возвращайся позже или сгенерируй новые уроки." />
        ) : null}

        {current ? (
          <div className={`ng-panel ${styles.card}`}>
            <div style={ui.text.muted}>
              {index + 1} / {items.length}
            </div>
            <div className={styles.word}>{current.word}</div>
            <div className={styles.translation}>{current.translation}</div>
            <div className={styles.context}>{current.context_sentence}</div>

            <div className={styles.actions}>
              {[1, 2, 3, 4, 5].map((r) => (
                <button key={r} type="button" disabled={review.isPending} onClick={() => onRate(r)}>
                  {r}
                </button>
              ))}
            </div>

            {review.error ? <ErrorState error={review.error} title="Ошибка сохранения" /> : null}
          </div>
        ) : null}
      </Card>
    </div>
  )
}
