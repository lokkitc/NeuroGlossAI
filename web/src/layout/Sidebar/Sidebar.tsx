import { NavLink } from 'react-router-dom'
import styles from './Sidebar.module.css'
import { navItems } from '../../constants/nav'
import { useAuthStore } from '../../store/authStore'
import { useUiStore } from '../../store/uiStore'
import Button from '../../components/ui/Button/Button'
import { Home, MessageCircle, PencilLine, User, LogIn, ExternalLink } from 'lucide-react'

export default function Sidebar() {
  const isAuthed = useAuthStore((s) => Boolean(s.accessToken))
  const collapsed = useUiStore((s) => s.sidebarCollapsed)
  const toggle = useUiStore((s) => s.toggleSidebar)

  const iconByKey: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
    home: Home,
    chat: MessageCircle,
    create: PencilLine,
    profile: User,
    login: LogIn,
  }

  const main = navItems.filter((i) => i.key !== 'profile')
  const account = navItems.filter((i) => i.key === 'profile')

  return (
    <aside className={collapsed ? styles.rootCollapsed : styles.root}>
      <div className={styles.top}>
        <div className={styles.brandRow}>
          <div className={styles.brandMark}>NG</div>
          {!collapsed ? <div className={styles.brandText}>NeuroGlossAI</div> : null}
        </div>
      </div>

      <div className={styles.middle}>
        {/* {!collapsed ? <div className={styles.sectionLabel}>Main</div> : null} */}
        <nav className={styles.nav}>
          {main
            .filter((i) => (i.protected ? isAuthed : true))
            .map((i, idx) => {
              const Icon = iconByKey[i.key] ?? ExternalLink
              return (
                <NavLink
                  key={i.key}
                  to={i.to}
                  className={({ isActive }) => {
                    const base = collapsed ? styles.itemCollapsed : styles.item
                    return isActive ? `${base} ${styles.active}` : base
                  }}
                >
                  <Icon className={styles.itemIcon} size={18} />
                  {!collapsed ? <div className={styles.itemLabel}>{i.label}</div> : null}
                  {!collapsed ? <div className={styles.itemMeta}>{String(idx + 1)}</div> : null}
                </NavLink>
              )
            })}
        </nav>

        {!collapsed ? <div className={styles.sectionLabel}>Account</div> : null}
        <nav className={styles.nav}>
          {account
            .filter((i) => (i.protected ? isAuthed : true))
            .map((i) => {
              const Icon = iconByKey[i.key] ?? User
              return (
                <NavLink
                  key={i.key}
                  to={i.to}
                  className={({ isActive }) => {
                    const base = collapsed ? styles.itemCollapsed : styles.item
                    return isActive ? `${base} ${styles.active}` : base
                  }}
                >
                  <Icon className={styles.itemIcon} size={18} />
                  {!collapsed ? <div className={styles.itemLabel}>{i.label}</div> : null}
                  {!collapsed ? <div className={styles.itemMeta}>A</div> : null}
                </NavLink>
              )
            })}

          {!isAuthed ? (
            <NavLink
              to='/login'
              className={({ isActive }) => {
                const base = collapsed ? styles.itemCollapsed : styles.item
                return isActive ? `${base} ${styles.active}` : base
              }}
            >
              <LogIn className={styles.itemIcon} size={18} />
              {!collapsed ? <div className={styles.itemLabel}>Login</div> : null}
              {!collapsed ? <div className={styles.itemMeta}>L</div> : null}
            </NavLink>
          ) : null}
        </nav>
      </div>

      <div className={styles.bottom}>
        <div className={styles.bottomRow}>
          <Button variant='ghost' onClick={toggle}>
            {collapsed ? '>' : '<'}
          </Button>
          <div className={styles.hint}>{collapsed ? 'v1' : 'NeuroGlossAI web v1'}</div>
        </div>
      </div>
    </aside>
  )
}
