import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ApiError } from '../../api/types'
import { authApi } from '../../api/auth'
import { useAuthStore } from '../../stores/authStore'
import { ui } from '../../styles/ui'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation() as { state?: { from?: string } }
  const setToken = useAuthStore((s) => s.setToken)

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      const res = await authApi.login({ username, password })
      setToken(res.access_token)
      const to = location.state?.from ?? '/'
      navigate(to, { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.requestId ? `${err.message} (запрос: ${err.requestId})` : err.message)
      } else {
        const msg = err instanceof Error ? err.message : String(err)
        setError(`Не удалось выполнить вход: ${msg}`)
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div>
      <h1 style={ui.mt.none}>Вход</h1>
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: ui.space.s3 }}>
        <label>
          Логин или почта
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
          {isSubmitting ? 'Вхожу…' : 'Войти'}
        </button>
      </form>
      <div style={{ marginTop: ui.space.s3, color: ui.color.muted }}>
        Нет аккаунта? <Link to="/register">Регистрация</Link>
      </div>
    </div>
  )
}
