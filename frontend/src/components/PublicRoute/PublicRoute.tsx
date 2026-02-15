import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'

export function PublicRoute() {
  const token = useAuthStore((s) => s.token)

  if (token) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
