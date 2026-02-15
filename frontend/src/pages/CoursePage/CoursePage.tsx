import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  useActiveCourse,
  useGenerateCourse,
  useGenerateFullCourse,
  useGenerateLesson,
} from '../../api/hooks'
import { Card } from '../../components/ui/Card/Card'
import { EmptyState } from '../../components/states/EmptyState/EmptyState'
import { ErrorState } from '../../components/states/ErrorState/ErrorState'
import { LoadingState } from '../../components/states/LoadingState/LoadingState'
import { ui } from '../../styles/ui'
import styles from './CoursePage.module.css'

function parseCsv(value: string): string[] {
  return value
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

type PathNode = {
  id: string
  sectionOrder: number
  unitOrder: number
  unitTopic: string
  levelOrder: number
  status: string
  stars: number
}

function isLocked(status: string): boolean {
  return String(status).toLowerCase() === 'locked'
}

function isCompleted(status: string): boolean {
  return String(status).toLowerCase() === 'completed'
}

export function CoursePage() {
  const navigate = useNavigate()

  const courseQ = useActiveCourse()
  const generateCourse = useGenerateCourse()
  const generateFull = useGenerateFullCourse()
  const generateLesson = useGenerateLesson()

  const [level, setLevel] = useState('A1')
  const [interestsCsv, setInterestsCsv] = useState('')
  const [maxTopics, setMaxTopics] = useState(3)

  const interests = useMemo(() => parseCsv(interestsCsv), [interestsCsv])

  const onGenerateCourse = async () => {
    await generateCourse.mutateAsync({ interests, level, regenerate: true })
  }

  const onGenerateFull = async () => {
    await generateFull.mutateAsync({
      interests,
      level,
      max_topics: maxTopics,
      regenerate_path: true,
      force_regenerate_lessons: false,
      generation_mode: 'balanced',
    })
  }

  const nodes: PathNode[] = useMemo(() => {
    const c = courseQ.data
    if (!c) return []

    const out: PathNode[] = []
    for (const sec of c.sections) {
      for (const unit of sec.units) {
        for (const lvl of unit.levels) {
          if (lvl.type !== 'lesson') continue
          out.push({
            id: lvl.id,
            sectionOrder: sec.order,
            unitOrder: unit.order,
            unitTopic: unit.topic,
            levelOrder: lvl.order,
            status: lvl.status,
            stars: lvl.stars,
          })
        }
      }
    }

    return out
  }, [courseQ.data])

  const activeNodeId = useMemo(() => {
    const firstUnlocked = nodes.find((n) => !isLocked(n.status))
    const firstNotCompleted = nodes.find((n) => !isLocked(n.status) && !isCompleted(n.status))
    return (firstNotCompleted ?? firstUnlocked)?.id ?? null
  }, [nodes])

  const activeNode = useMemo(() => nodes.find((n) => n.id === activeNodeId) ?? null, [nodes, activeNodeId])

  const startNode = async (node: PathNode) => {
    if (isLocked(node.status)) return
    const cefr = courseQ.data?.cefr_level ?? level
    const lesson = await generateLesson.mutateAsync({
      level_template_id: node.id,
      topic: node.unitTopic,
      level: cefr,
      generation_mode: 'balanced',
    })
    navigate(`/lessons/${lesson.id}`)
  }

  // Смещения нод относительно центральной оси, выведены из figma-экспорта 9_1212.
  // Это даёт «дугу» вправо в начале и уход влево ниже.
  const nodeOffsetsFromCenterPx = [0, 46, 69, 46, -1, -47, -72, -48] as const
  const nodeStepY = 86
  const topStart = 32
  const bottomSheetReserve = 170
  const pathHeight = Math.max(520, topStart + nodes.length * nodeStepY + bottomSheetReserve)

  return (
    <div className={styles.grid}>
      <Card title="Курс">
        {courseQ.isLoading ? <LoadingState title="Загружаю курс…" /> : null}
        {courseQ.error ? <ErrorState error={courseQ.error} onRetry={() => courseQ.refetch()} /> : null}

        {!courseQ.isLoading && !courseQ.error && !courseQ.data ? (
          <EmptyState title="Активного курса нет" description="Сгенерируй курс в панели справа." />
        ) : null}

        {courseQ.data ? (
          <>
            <div style={ui.text.muted}>
              Язык: {courseQ.data.target_language} · Уровень: {courseQ.data.cefr_level}
              {courseQ.data.theme ? ` · Тема: ${courseQ.data.theme}` : ''}
            </div>

            {nodes.length === 0 ? (
              <EmptyState title="Путь пуст" description="Сгенерируй курс заново или проверь шаблон." />
            ) : (
              <div className={styles.path} style={{ minHeight: pathHeight }}>
                <div className={styles.track} aria-hidden="true" />

                {nodes.map((n, idx) => {
                  const locked = isLocked(n.status)
                  const done = isCompleted(n.status)
                  const active = n.id === activeNodeId
                  const nodeClass = locked
                    ? `${styles.node} ${styles.nodeLocked}`
                    : active
                      ? `${styles.node} ${styles.nodeActive}`
                      : done
                        ? `${styles.node} ${styles.nodeDone}`
                        : styles.node

                  const innerClass = locked ? `${styles.nodeInner} ${styles.nodeInnerLocked}` : styles.nodeInner

                  const offset = nodeOffsetsFromCenterPx[idx % nodeOffsetsFromCenterPx.length]
                  const top = topStart + idx * nodeStepY
                  const left = `calc(50% + ${offset}px)`

                  return (
                    <button
                      key={n.id}
                      type="button"
                      className={nodeClass}
                      style={{ top, left }}
                      onClick={() => (locked ? undefined : startNode(n))}
                      disabled={generateLesson.isPending || locked}
                      title={locked ? 'Заблокировано' : 'Открыть'}
                    >
                      <div className={innerClass}>{done ? '★' : active ? '▶' : n.levelOrder}</div>
                    </button>
                  )
                })}

                {activeNode ? (
                  <div className={styles.sheet}>
                    <div className={styles.sheetTitle}>{activeNode.unitTopic}</div>
                    <div className={styles.sheetSub}>
                      Раздел {activeNode.sectionOrder}, юнит {activeNode.unitOrder} · Урок {activeNode.levelOrder} · ★{activeNode.stars}
                    </div>
                    <button
                      type="button"
                      className={styles.start}
                      onClick={() => startNode(activeNode)}
                      disabled={generateLesson.isPending}
                    >
                      {generateLesson.isPending ? 'Генерирую…' : 'START'}
                    </button>
                  </div>
                ) : null}
              </div>
            )}
          </>
        ) : null}
      </Card>

      <Card title="Генерация">
        <form className={styles.form} onSubmit={(e) => e.preventDefault()}>
          <label>
            Уровень CEFR
            <select value={level} onChange={(e) => setLevel(e.target.value)}>
              <option value="A1">A1</option>
              <option value="A2">A2</option>
              <option value="B1">B1</option>
              <option value="B2">B2</option>
              <option value="C1">C1</option>
            </select>
          </label>

          <label>
            Интересы (через запятую)
            <input value={interestsCsv} onChange={(e) => setInterestsCsv(e.target.value)} placeholder="Travel, Music" />
          </label>

          <div className={styles.actions}>
            <button
              type="button"
              onClick={onGenerateCourse}
              disabled={generateCourse.isPending || generateFull.isPending}
            >
              {generateCourse.isPending ? 'Генерирую…' : 'Сгенерировать курс'}
            </button>

            <button
              type="button"
              onClick={onGenerateFull}
              disabled={generateCourse.isPending || generateFull.isPending}
            >
              {generateFull.isPending ? 'Генерирую…' : 'Курс + уроки'}
            </button>
          </div>

          <label>
            Сколько тем для generate-full
            <input
              type="number"
              min={1}
              max={10}
              value={maxTopics}
              onChange={(e) => setMaxTopics(Number(e.target.value || 1))}
            />
          </label>

          {generateCourse.error ? <ErrorState error={generateCourse.error} title="Ошибка генерации" /> : null}
          {generateFull.error ? <ErrorState error={generateFull.error} title="Ошибка генерации" /> : null}
        </form>
      </Card>
    </div>
  )
}
