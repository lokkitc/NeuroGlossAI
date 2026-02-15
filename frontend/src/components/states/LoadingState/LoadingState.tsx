import styles from './LoadingState.module.css'

export function LoadingState(props: { title?: string }) {
  return (
    <div className={styles.root}>
      <div className={styles.spinner} aria-hidden="true" />
      <div className={styles.text}>{props.title ?? 'Загрузка…'}</div>
    </div>
  )
}
