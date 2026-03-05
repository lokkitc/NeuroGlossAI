export type NavItem = {
  key: string
  label: string
  to: string
  protected?: boolean
}

export const navItems: NavItem[] = [
  { key: 'home', label: 'Home', to: '/' },
  { key: 'chat', label: 'Chat', to: '/chat', protected: true },
  { key: 'create', label: 'Create', to: '/characters/new', protected: true },
  { key: 'profile', label: 'Profile', to: '/profile', protected: true },
]
