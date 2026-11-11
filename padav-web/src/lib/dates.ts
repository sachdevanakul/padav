/** The API sends naive UTC timestamps ("2026-11-11T06:22:00"); without a zone JS would read them as local time. */
export function parseServerDate(value: string): Date {
  return new Date(/(?:Z|[+-]\d{2}:?\d{2})$/.test(value) ? value : `${value}Z`)
}

export function formatDateTime(value: string, language: string): string {
  return new Intl.DateTimeFormat(language === 'hi' ? 'hi-IN' : 'en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' }).format(parseServerDate(value))
}

export function formatClock(totalSeconds: number): string {
  const safe = Math.max(0, Math.floor(totalSeconds))
  const h = Math.floor(safe / 3600)
  const m = Math.floor((safe % 3600) / 60)
  const s = safe % 60
  const mm = String(m).padStart(2, '0')
  const ss = String(s).padStart(2, '0')
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`
}
