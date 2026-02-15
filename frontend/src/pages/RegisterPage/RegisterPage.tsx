import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../../api/types'
import { authApi } from '../../api/auth'
import { useAuthStore } from '../../stores/authStore'
import { ui } from '../../styles/ui'

export function RegisterPage() {
  const navigate = useNavigate()
  const setToken = useAuthStore((s) => s.setToken)

  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      await authApi.register({ email, username, password })
      const token = await authApi.login({ username, password })
      setToken(token.access_token)
      navigate('/', { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.requestId ? `${err.message} (запрос: ${err.requestId})` : err.message)
      } else {
        setError('Не удалось выполнить регистрацию')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div>
      <h1 style={ui.mt.none}>Регистрация</h1>
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: ui.space.s3 }}>
        <label>
          Почта
          <input value={email} onChange={(e) => setEmail(e.target.value)} required type="email" />
        </label>
        <label>
          Имя пользователя
          <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        </label>
        <label>
          Пароль
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            type="password"
          />
        </label>
        {error ? (
          <div style={{ color: ui.color.danger }} role="alert">
            {error}
          </div>
        ) : null}
        <button disabled={isSubmitting} type="submit">
          {isSubmitting ? 'Создаю…' : 'Создать аккаунт'}
        </button>
      </form>
      <div style={{ marginTop: ui.space.s3, color: ui.color.muted }}>
        Уже есть аккаунт? <Link to="/login">Войти</Link>
      </div>
    </div>
  )
}
