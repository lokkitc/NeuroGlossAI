import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useActiveCourse, useGenerateLesson, useLessonsList } from '../../api/hooks'
import { Card } from '../../components/ui/Card/Card'
import { EmptyState } from '../../components/states/EmptyState/EmptyState'
import { ErrorState } from '../../components/states/ErrorState/ErrorState'
import { LoadingState } from '../../components/states/LoadingState/LoadingState'
import { formatDateTime } from '../../utils/format'
import { ui } from '../../styles/ui'
import styles from './LessonsPage.module.css'

type LessonOption = { levelTemplateId: string; topic: string; label: string; isLocked: boolean }

export function LessonsPage() {
  const navigate = useNavigate()
  const lessonsQ = useLessonsList({ skip: 0, limit: 50 })
  const courseQ = useActiveCourse()
  const gen = useGenerateLesson()

  const options: LessonOption[] = useMemo(() => {
    const c = courseQ.data
    if (!c) return []
    const out: LessonOption[] = []
    for (const sec of c.sections) {
      for (const unit of sec.units) {
        for (const lvl of unit.levels) {
          if (lvl.type !== 'lesson') continue
          const isLocked = String(lvl.status).toLowerCase() === 'locked'
          out.push({
            levelTemplateId: lvl.id,
            topic: unit.topic,
            label: `${sec.order}.${unit.order} ${unit.topic} (урок #${lvl.order}, ${lvl.status})`,
            isLocked,
          })
        }
      }
    }
    return out
  }, [courseQ.data])

  const [topic, setTopic] = useState('')
  const [levelTemplateId, setLevelTemplateId] = useState('')
  const [level, setLevel] = useState('A1')

  const onSelectPreset = (id: string) => {
    setLevelTemplateId(id)
    const found = options.find((o) => o.levelTemplateId === id)
    if (found) setTopic(found.topic)
  }

  const onGenerate = async () => {
    const lesson = await gen.mutateAsync({
      level_template_id: levelTemplateId,
      topic,
      level,
      generation_mode: 'balanced',
    })
    navigate(`/lessons/${lesson.id}`)
  }

  return (
    <div className={styles.grid}>
      <Card title="Уроки">
        <div className={styles.header}>
          <div style={ui.text.muted}>
            История генераций
          </div>
          <button type="button" onClick={() => lessonsQ.refetch()} disabled={lessonsQ.isFetching}>
            Обновить
          </button>
        </div>

        {lessonsQ.isLoading ? <LoadingState title="Загружаю уроки…" /> : null}
        {lessonsQ.error ? <ErrorState error={lessonsQ.error} onRetry={() => lessonsQ.refetch()} /> : null}

        {lessonsQ.data && lessonsQ.data.length === 0 ? (
          <EmptyState title="Уроков пока нет" description="Сгенерируй первый урок справа." />
        ) : null}

        {lessonsQ.data && lessonsQ.data.length > 0 ? (
          <div className={styles.list}>
            {lessonsQ.data.map((l) => (
              <div key={l.id} className={styles.item}>
                <div>
                  <div style={ui.text.title}>
                    <Link to={`/lessons/${l.id}`}>{l.topic_snapshot || 'Урок'}</Link>
                  </div>
                  <div className={styles.meta}>
                    {formatDateTime(l.created_at)} · качество: {l.quality_status} · слов: {l.vocabulary_items.length}
                  </div>
                </div>
                <div>
                  <Link to={`/lessons/${l.id}`}>Открыть</Link>
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </Card>

      <Card title="Сгенерировать урок">
        <form className={styles.form} onSubmit={(e) => e.preventDefault()}>
          <label>
            Предустановка (из курса)
            <select value={levelTemplateId} onChange={(e) => onSelectPreset(e.target.value)}>
              <option value="">— выбрать —</option>
              {options.map((o) => (
                <option key={o.levelTemplateId} value={o.levelTemplateId} disabled={o.isLocked}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            level_template_id
            <input value={levelTemplateId} onChange={(e) => setLevelTemplateId(e.target.value)} placeholder="UUID" />
          </label>

          <label>
            Тема
            <input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Например: Travel" />
          </label>

          <label>
            Уровень
            <select value={level} onChange={(e) => setLevel(e.target.value)}>
              <option value="A1">A1</option>
              <option value="A2">A2</option>
              <option value="B1">B1</option>
              <option value="B2">B2</option>
              <option value="C1">C1</option>
            </select>
          </label>

          <button
            type="button"
            onClick={onGenerate}
            disabled={!levelTemplateId || !topic || gen.isPending}
            title={!levelTemplateId || !topic ? 'Заполни level_template_id и тему' : 'Сгенерировать'}
          >
            {gen.isPending ? 'Генерирую…' : 'Сгенерировать'}
          </button>

          {gen.error ? <ErrorState error={gen.error} title="Ошибка генерации" /> : null}
          {courseQ.isError ? (
            <div style={ui.text.mutedOnly}>Курс не найден — предустановки недоступны.</div>
          ) : null}
        </form>
      </Card>
    </div>
  )
}
