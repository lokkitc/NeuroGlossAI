import Card from '../../ui/Card/Card'
import styles from './ErrorState.module.css'

type Props = {
  title?: string
  message: string
  onRetry?: () => void
}

export default function ErrorState({ title = 'Something went wrong', message, onRetry }: Props) {
  return (
    <Card className={styles.card}>
      <div className={styles.title}>{title}</div>
      <div className={styles.msg}>{message}</div>
      {onRetry ? (
        <button className={styles.retry} onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </Card>
  )
}
