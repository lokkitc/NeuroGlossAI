import styles from './LoadingState.module.css'

type Props = {
  lines?: number
}

export default function LoadingState({ lines = 3 }: Props) {
  return (
    <div className={styles.root}>
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className={styles.line} />
      ))}
    </div>
  )
}
