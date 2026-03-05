import { Outlet } from 'react-router-dom'
import styles from './AuthLayout.module.css'

export default function AuthLayout() {
  return (
    <div className={styles.root}>
      <main className={styles.main}>
        <div className={styles.card}>
          <div className={styles.brand}>NeuroGlossAI</div>
          <Outlet />
        </div>
      </main>
    </div>
  )
}
