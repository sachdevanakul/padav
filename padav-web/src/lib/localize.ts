export function pickText(language: string, en: string | null | undefined, hi: string | null | undefined): string {
  return language === 'hi' && hi ? hi : en ?? ''
}

export function formatMarks(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2).replace(/0+$/, '').replace(/\.$/, '')
}
