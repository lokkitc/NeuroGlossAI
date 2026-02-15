import { useMemo, useState } from 'react'
import { useRoleplayChat } from '../../api/hooks'
import { Card } from '../../components/ui/Card/Card'
import { ErrorState } from '../../components/states/ErrorState/ErrorState'
import { ui } from '../../styles/ui'
import styles from './RoleplayPage.module.css'

type Msg = { role: 'user' | 'assistant'; content: string }

export function RoleplayPage() {
  const chat = useRoleplayChat()

  const [scenario, setScenario] = useState('Café')
  const [role, setRole] = useState('Customer')
  const [targetLanguage, setTargetLanguage] = useState('English')
  const [level, setLevel] = useState('A1')
  const [message, setMessage] = useState('')
  const [thread, setThread] = useState<Msg[]>([])

  const history = useMemo(() => thread.map((m) => ({ role: m.role, content: m.content })), [thread])

  const onSend = async () => {
    const trimmed = message.trim()
    if (!trimmed) return

    setMessage('')
    setThread((t) => [...t, { role: 'user', content: trimmed }])

    try {
      const res = await chat.mutateAsync({
        scenario,
        role,
        message: trimmed,
        history,
        target_language: targetLanguage,
        level,
      })
      setThread((t) => [...t, { role: 'assistant', content: res.response }])
    } catch {
      // ошибка будет показана ниже
    }
  }

  const onReset = () => {
    if (!window.confirm('Очистить чат?')) return
    setThread([])
  }

  return (
    <div className={styles.grid}>
      <Card title="Параметры">
        <form className={styles.form} onSubmit={(e) => e.preventDefault()}>
          <label>
            Сценарий
            <input value={scenario} onChange={(e) => setScenario(e.target.value)} />
          </label>
          <label>
            Роль
            <input value={role} onChange={(e) => setRole(e.target.value)} />
          </label>
          <label>
            Целевой язык
            <input value={targetLanguage} onChange={(e) => setTargetLanguage(e.target.value)} />
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

          <div style={ui.rowWrap}>
            <button type="button" onClick={onReset} disabled={chat.isPending}>
              Очистить
            </button>
          </div>
        </form>
      </Card>

      <Card title="Чат">
        <div className={styles.thread}>
          {thread.length === 0 ? (
            <div style={ui.text.mutedOnly}>
              Напиши сообщение, чтобы начать диалог.
            </div>
          ) : null}

          {thread.map((m, i) => (
            <div key={i} className={m.role === 'user' ? styles.msgUser : styles.msgAi}>
              <div style={{ ...ui.text.title, ...ui.mb.s2 }}>
                {m.role === 'user' ? 'Ты' : 'ИИ'}
              </div>
              <div>{m.content}</div>
            </div>
          ))}

          {chat.error ? <ErrorState error={chat.error} title="Ошибка" /> : null}
        </div>

        <div style={{ ...ui.mt.s3, ...ui.rowWrap }}>
          <input
            style={ui.inputGrow}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Твоё сообщение…"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                void onSend()
              }
            }}
          />
          <button type="button" onClick={onSend} disabled={chat.isPending}>
            {chat.isPending ? 'Отправляю…' : 'Отправить'}
          </button>
        </div>
      </Card>
    </div>
  )
}
