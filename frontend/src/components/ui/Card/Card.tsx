import clsx from 'clsx'
import styles from './Card.module.css'

export function Card(props: { title?: string; className?: string; children: React.ReactNode }) {
  return (
    <section className={clsx('ng-panel', styles.root, props.className)}>
      {props.title ? <div className={styles.title}>{props.title}</div> : null}
      <div className={styles.body}>{props.children}</div>
    </section>
  )
}
