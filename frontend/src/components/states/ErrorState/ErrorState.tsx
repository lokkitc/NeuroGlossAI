import { ApiError } from '../../../api/types'
import styles from './ErrorState.module.css'

export function ErrorState(props: { error: unknown; title?: string; onRetry?: () => void }) {
  const message = (() => {
    if (props.error instanceof ApiError) {
      return props.error.requestId
        ? `${props.error.message} (запрос: ${props.error.requestId})`
        : props.error.message
    }
    if (props.error instanceof Error) return props.error.message
    return String(props.error)
  })()

  return (
    <div className={styles.root} role="alert">
      <div className={styles.title}>{props.title ?? 'Ошибка'}</div>
      <div className={styles.msg}>{message}</div>
      {props.onRetry ? (
        <button type="button" onClick={props.onRetry} className={styles.retry}>
          Повторить
        </button>
      ) : null}
    </div>
  )
}
