import styles from './EmptyState.module.css'

export function EmptyState(props: { title: string; description?: string }) {
  return (
    <div className={styles.root}>
      <div className={styles.title}>{props.title}</div>
      {props.description ? <div className={styles.desc}>{props.description}</div> : null}
    </div>
  )
}
