import styles from './Field.module.css'

type Props = {
  label: string
  hint?: string
  error?: string | null
  children: React.ReactNode
}

export default function Field({ label, hint, error, children }: Props) {
  return (
    <label className={styles.root}>
      <div className={styles.top}>
        <div className={styles.label}>{label}</div>
        {hint ? <div className={styles.hint}>{hint}</div> : null}
      </div>
      {children}
      {error ? <div className={styles.error}>{error}</div> : null}
    </label>
  )
}
