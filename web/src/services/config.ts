export function getApiBaseUrl() {
  const v = (import.meta as any).env?.VITE_API_BASE_URL as string | undefined
  if (v && v.trim()) return v.trim()
  if ((import.meta as any).env?.DEV) return '/api/v1'
  return 'https://neuroglossai-production.up.railway.app/api/v1'
}

export function getAppVersion() {
  const v = (import.meta as any).env?.VITE_APP_VERSION as string | undefined
  return (v && v.trim()) || 'web'
}
