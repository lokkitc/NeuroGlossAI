import { useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import * as auth from '../../services/auth'
import { getErrorMessage } from '../../services/http'
import Card from '../../components/ui/Card/Card'
import Field from '../../components/ui/Field/Field'
import Button from '../../components/ui/Button/Button'
import styles from './LoginPage.module.css'

export default function LoginPage() {
  const nav = useNavigate()
  const location = useLocation() as any

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const from = useMemo(() => location?.state?.from || '/chat', [location])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (!username.trim() || !password) {
      setError('Enter username and password')
      return
    }

    setIsLoading(true)
    try {
      await auth.login({ username, password })

      nav(from, { replace: true })
    } catch (e: any) {
      setError(getErrorMessage(e, 'Login failed'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className={styles.card}>
      <h1 className={styles.title}>Login</h1>
      <form onSubmit={onSubmit} className={styles.form}>
        <Field label='Username'>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder='Username'
            autoComplete='username'
          />
        </Field>
        <Field label='Password'>
          <input
            type='password'
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder='Password'
            autoComplete='current-password'
          />
        </Field>
        <div className={styles.actions}>
          <Button type='submit' disabled={isLoading}>
            {isLoading ? 'Signing in…' : 'Sign in'}
          </Button>
        </div>
        {error ? <div className={styles.error}>{error}</div> : null}
      </form>
    </Card>
  )
}
