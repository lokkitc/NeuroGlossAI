export function formatDateTime(value: string | number | Date): string {
  const d = typeof value === 'string' || typeof value === 'number' ? new Date(value) : value
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleString()
}

export function clampInt(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, Math.trunc(value)))
}
