import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Check, LogOut, Settings as SettingsIcon } from 'lucide-react'
import AppShell from '../layouts/AppShell'
import { api } from '../services/api'
import { translations } from '../locales/translations'
import { authStore } from '../store/auth'
import { preferencesStore, type Language, type Theme } from '../store/preferences'
import '../styles/account.css'

type PasswordForm = { current: string; next: string; confirm: string }
type PasswordErrors = Partial<Record<keyof PasswordForm, string>>

const byteLength = (value: string) => new TextEncoder().encode(value).length

export function validatePasswordChange(form: PasswordForm, t: Record<string, string>): PasswordErrors {
  const errors: PasswordErrors = {}
  if (!form.current) errors.current = t.currentPassword
  if (form.next.length < 8 || byteLength(form.next) > 72) errors.next = t.errPasswordLength
  else if (form.next === form.current) errors.next = t.errPasswordSame
  if (form.confirm !== form.next) errors.confirm = t.errPasswordMatch
  return errors
}

export default function SettingsPage() {
  const { language, theme, setLanguage, setTheme } = preferencesStore()
  const t = translations[language]
  const navigate = useNavigate()
  const refreshToken = authStore((state) => state.refreshToken)
  const [form, setForm] = useState<PasswordForm>({ current: '', next: '', confirm: '' })
  const [errors, setErrors] = useState<PasswordErrors>({})

  // Preferences apply immediately on this device; syncing to the account is best-effort.
  function choose(next: { language?: Language; theme?: Theme }) {
    if (next.language) setLanguage(next.language)
    if (next.theme) setTheme(next.theme)
    void api.updateMe(next).catch(() => undefined)
  }

  const change = useMutation({
    mutationFn: () => api.changePassword(form.current, form.next),
    onSuccess: (tokens) => { authStore.getState().setTokens(tokens.access_token, tokens.refresh_token); setForm({ current: '', next: '', confirm: '' }) },
  })

  function submit(event: FormEvent) {
    event.preventDefault()
    change.reset()
    const found = validatePasswordChange(form, t)
    setErrors(found)
    if (Object.keys(found).length === 0) change.mutate()
  }
  async function signOut() {
    if (refreshToken) await api.logout(refreshToken).catch(() => undefined)
    authStore.getState().clear()
    navigate('/auth/login', { replace: true })
  }
  const set = (key: keyof PasswordForm) => (value: string) => setForm((prev) => ({ ...prev, [key]: value }))

  return <AppShell>
    <section className="page-heading"><p className="eyebrow"><SettingsIcon size={14} /> PADAV SETTINGS</p><h1>{t.settingsTitle}</h1><p className="muted">{t.settingsSubtitle}</p></section>
    <div className="acct-grid">
      <section className="acct-card card" aria-labelledby="appearance-heading">
        <h2 id="appearance-heading">{t.appearance}</h2>
        <Segmented label={t.languageLabel} value={language} onChange={(value) => choose({ language: value as Language })} options={[['en', 'English'], ['hi', 'हिन्दी']]} />
        <Segmented label={t.themeLabel} value={theme} onChange={(value) => choose({ theme: value as Theme })} options={[['dark', t.themeDark], ['light', t.themeLight]]} />
      </section>

      <form className="acct-card card" onSubmit={submit} noValidate aria-labelledby="security-heading">
        <h2 id="security-heading">{t.security}</h2>
        <PasswordField id="pw-current" label={t.currentPassword} value={form.current} autoComplete="current-password" error={errors.current} onChange={set('current')} />
        <PasswordField id="pw-new" label={t.newPassword} value={form.next} autoComplete="new-password" error={errors.next} onChange={set('next')} hint={t.passwordHint} />
        <PasswordField id="pw-confirm" label={t.confirmNewPassword} value={form.confirm} autoComplete="new-password" error={errors.confirm} onChange={set('confirm')} />
        {change.isError && <p className="tx-error" role="alert">{(change.error as Error).message}</p>}
        <div className="acct-actions">
          <button className="button button-primary" disabled={change.isPending}>{t.updatePassword}</button>
          {change.isSuccess && <span className="acct-ok" role="status"><Check size={14} />{t.passwordUpdated}</span>}
        </div>
      </form>

      <section className="acct-card card" aria-labelledby="session-heading">
        <h2 id="session-heading">{t.accountSession}</h2>
        <button className="button button-secondary" onClick={() => void signOut()}><LogOut size={15} />{t.signOutLabel}</button>
      </section>
    </div>
  </AppShell>
}

function Segmented({ label, value, options, onChange }: { label: string; value: string; options: [string, string][]; onChange: (value: string) => void }) {
  return <div className="acct-field"><span id={`seg-${label}`}>{label}</span>
    <div className="acct-segmented" role="radiogroup" aria-labelledby={`seg-${label}`}>
      {options.map(([id, text]) => <button key={id} type="button" role="radio" aria-checked={value === id} className={value === id ? 'is-active' : ''} onClick={() => onChange(id)}>{text}</button>)}
    </div></div>
}

function PasswordField({ id, label, value, error, hint, autoComplete, onChange }: { id: string; label: string; value: string; error?: string; hint?: string; autoComplete: string; onChange: (value: string) => void }) {
  return <div className="acct-field"><label htmlFor={id}>{label}</label>
    <input id={id} type="password" value={value} autoComplete={autoComplete} maxLength={128} onChange={(e) => onChange(e.target.value)} aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-err` : undefined} />
    {hint && !error && <small className="muted">{hint}</small>}
    {error && <small className="acct-error" id={`${id}-err`} role="alert">{error}</small>}</div>
}
