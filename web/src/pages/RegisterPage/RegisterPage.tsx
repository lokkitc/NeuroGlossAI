import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import * as auth from '../../services/auth'
import { getErrorMessage } from '../../services/http'
import Card from '../../components/ui/Card/Card'
import Field from '../../components/ui/Field/Field'
import Button from '../../components/ui/Button/Button'
import styles from './RegisterPage.module.css'

export default function RegisterPage() {
  const nav = useNavigate()

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    setIsLoading(true)
    try {
      await auth.register({ username, email, password })

      nav('/login', { replace: true })
    } catch (e: any) {
      setError(getErrorMessage(e, 'Register failed'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className={styles.card}>
      <h1 className={styles.title}>Register</h1>
      <form onSubmit={onSubmit} className={styles.form}>
        <Field label='Username'>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder='Username'
            autoComplete='username'
          />
        </Field>
        <Field label='Email'>
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder='Email'
            autoComplete='email'
          />
        </Field>
        <Field label='Password'>
          <input
            type='password'
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder='Password (min 8 chars)'
            autoComplete='new-password'
          />
        </Field>
        <div className={styles.actions}>
          <Button type='submit' disabled={isLoading}>
            {isLoading ? 'Creating…' : 'Create account'}
          </Button>
        </div>
        {error ? <div className={styles.error}>{error}</div> : null}
      </form>
    </Card>
  )
}
