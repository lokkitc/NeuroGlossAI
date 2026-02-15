import { NavLink, Outlet } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { ui } from '../../styles/ui'
import styles from './AppLayout.module.css'

export function AppLayout() {
  const logout = useAuthStore((s) => s.logout)
  const me = useAuthStore((s) => s.me)
  const loadMe = useAuthStore((s) => s.loadMe)

  useEffect(() => {
    void loadMe()
  }, [loadMe])

  return (
    <div>
      <header className={styles.header}>
        <div className={`ng-container ${styles.headerInner}`}>
          <div className={styles.brand}>NeuroGlossAI</div>
          <nav className={styles.nav}>
            <NavLink to="/course" className={styles.link}>
              Курс
            </NavLink>
            <NavLink to="/lessons" className={styles.link}>
              Уроки
            </NavLink>
            <NavLink to="/review" className={styles.link}>
              Повторение
            </NavLink>
            <NavLink to="/roleplay" className={styles.link}>
              Ролевая
            </NavLink>
            <NavLink to="/settings" className={styles.link}>
              Настройки
            </NavLink>
          </nav>
          <div className={styles.user}>
            {me ? (
              <span title={me.email}>
                {me.username} · {me.xp} XP
              </span>
            ) : (
              <span style={ui.text.mutedOnly}>…</span>
            )}
          </div>
          <button className={styles.logout} onClick={logout} type="button">
            Выйти
          </button>
        </div>
      </header>

      <main className="ng-container ng-page">
        <Outlet />
      </main>
    </div>
  )
}
