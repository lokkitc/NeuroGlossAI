import { type ReactNode, useId } from 'react'
import styles from './Tabs.module.css'

export type TabItem = {
  id: string
  label: string
  content: ReactNode
}

export function Tabs(props: { items: TabItem[]; value: string; onChange: (id: string) => void }) {
  const baseId = useId()
  const active = props.items.find((i) => i.id === props.value) ?? props.items[0]

  return (
    <div>
      <div className={styles.list} role="tablist" aria-label="tabs">
        {props.items.map((item) => (
          <button
            key={item.id}
            type="button"
            className={item.id === active.id ? styles.tabActive : styles.tab}
            role="tab"
            aria-selected={item.id === active.id}
            aria-controls={`${baseId}-${item.id}`}
            onClick={() => props.onChange(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div id={`${baseId}-${active.id}`} role="tabpanel" className={styles.panel}> 
        {active.content}
      </div>
    </div>
  )
}
