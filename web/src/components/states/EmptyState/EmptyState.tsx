import Card from '../../ui/Card/Card'
import styles from './EmptyState.module.css'

type Props = {
  title: string
  message?: string
}

export default function EmptyState({ title, message }: Props) {
  return (
    <Card className={styles.card}>
      <div className={styles.title}>{title}</div>
      {message ? <div className={styles.msg}>{message}</div> : null}
    </Card>
  )
}
