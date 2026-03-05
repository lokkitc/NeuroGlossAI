import { Outlet } from 'react-router-dom'
import Sidebar from '../Sidebar/Sidebar'
import styles from './AppShell.module.css'

export default function AppShell() {
  return (
    <div className={styles.root}>
      <Sidebar />
      <div className={styles.content}>
        <header className={styles.header}>
          <div className={styles.headerInner}>
            <div className={styles.searchWrap}>
              <input className={styles.search} placeholder='Search…' />
            </div>
            <div className={styles.profile}>
              <div className={styles.avatar} />
            </div>
          </div>
          <div className={styles.headerBottom}></div>
          
        </header>

        <main className={styles.main}>
          <div className={styles.container}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
