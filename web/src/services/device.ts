import { useAuthStore } from '../store/authStore'

function randomId() {
  try {
    return crypto.randomUUID()
  } catch {
    return `${Date.now()}-${Math.random().toString(16).slice(2)}`
  }
}

export function ensureDeviceId() {
  const s = useAuthStore.getState()
  if (s.deviceId) return s.deviceId
  const id = randomId()
  s.setDeviceId(id)
  return id
}
