import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import Card from '../../components/ui/Card/Card'
import Button from '../../components/ui/Button/Button'
import LoadingState from '../../components/states/LoadingState/LoadingState'
import ErrorState from '../../components/states/ErrorState/ErrorState'
import * as auth from '../../services/auth'
import { getErrorMessage } from '../../services/http'
import styles from './ProfilePage.module.css'

export default function ProfilePage() {
  const nav = useNavigate()

  const meQ = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: () => auth.me(),
  })

  const logoutM = useMutation({
    mutationFn: () => auth.logout(),
    onSuccess: () => {
      nav('/login', { replace: true })
    },
  })

  const logoutErr = logoutM.isError ? getErrorMessage(logoutM.error, 'Logout failed') : null

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <h1 className={styles.title}>Profile</h1>
        <div className={styles.subtitle}>Account and subscription status.</div>
      </div>

      {meQ.isLoading ? <LoadingState lines={6} /> : null}
      {meQ.isError ? (
        <ErrorState message={(meQ.error as any)?.message || 'Failed to load profile'} onRetry={() => meQ.refetch()} />
      ) : null}

      {meQ.isSuccess ? (
        <Card className={styles.card}>
          <div className={styles.row}>
            <div className={styles.k}>Username</div>
            <div className={styles.v}>{meQ.data.username}</div>
          </div>
          <div className={styles.row}>
            <div className={styles.k}>Email</div>
            <div className={styles.v}>{meQ.data.email}</div>
          </div>
          <div className={styles.row}>
            <div className={styles.k}>Tier</div>
            <div className={styles.v}>{meQ.data.subscription_tier}</div>
          </div>
          <div className={styles.row}>
            <div className={styles.k}>XP / Level</div>
            <div className={styles.v}>
              {meQ.data.xp} / {meQ.data.level}
            </div>
          </div>

          <div className={styles.actions}>
            <Button variant='danger' disabled={logoutM.isPending} onClick={() => logoutM.mutate()}>
              {logoutM.isPending ? 'Logging out…' : 'Logout'}
            </Button>
          </div>
          {logoutErr ? <div className={styles.error}>{logoutErr}</div> : null}
        </Card>
      ) : null}
    </div>
  )
}
