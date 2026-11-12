import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Brain, Clock3, ShieldCheck } from 'lucide-react'
import AppShell from '../layouts/AppShell'
import { ApiError, api } from '../services/api'
import { translations } from '../locales/translations'
import { preferencesStore } from '../store/preferences'
import '../styles/pia.css'

export function validateConsent(form: { age: string; guardian: boolean; accepted: boolean }, t: Record<string, string>) {
  const errors: { age?: string; guardian?: string; accepted?: string } = {}
  const age = Number(form.age)
  if (!form.age.trim() || !Number.isInteger(age) || age < 13 || age > 120) errors.age = t.piaErrAge
  else if (age < 18 && !form.guardian) errors.guardian = t.piaErrGuardian
  if (!form.accepted) errors.accepted = t.piaErrAccept
  return errors
}

export default function PiaPage() {
  const language = preferencesStore((state) => state.language)
  const t = translations[language]
  const navigate = useNavigate()
  const [needsConsent, setNeedsConsent] = useState(false)
  const [form, setForm] = useState({ age: '', guardian: false, accepted: false })
  const [errors, setErrors] = useState<ReturnType<typeof validateConsent>>({})

  // Starting resumes any open session; the server answers 403 until consent has been recorded.
  const start = useMutation({
    mutationFn: () => api.piaStart(language),
    onSuccess: (session) => navigate(`/pia/sessions/${session.id}`),
    onError: (error) => { if (error instanceof ApiError && error.status === 403) setNeedsConsent(true) },
  })
  const consent = useMutation({
    mutationFn: async () => { await api.piaConsent(Number(form.age), form.guardian); return api.piaStart(language) },
    onSuccess: (session) => navigate(`/pia/sessions/${session.id}`),
  })

  function submit(event: FormEvent) {
    event.preventDefault()
    const found = validateConsent(form, t)
    setErrors(found)
    if (Object.keys(found).length === 0) consent.mutate()
  }
  const failure = [start, consent].find((m) => m.isError && !(m === start && needsConsent))
  const age = Number(form.age)

  return <AppShell>
    <section className="page-heading"><p className="eyebrow"><Brain size={14} /> PIA</p><h1>{t.piaTitle}</h1><p className="muted">{t.piaSubtitle}</p></section>
    <div className="pia-grid">
      <section className="card pia-card" aria-labelledby="pia-about">
        <p className="pia-banner" role="note"><ShieldCheck size={16} />{t.piaExperimental}</p>
        <h2 id="pia-about"><Clock3 size={16} /> {t.piaFacts}</h2>
        <ul className="pia-rules">{['piaRule1', 'piaRule2', 'piaRule3', 'piaRule4'].map((key) => <li key={key}>{t[key]}</li>)}</ul>
        {!needsConsent && <button className="button button-primary" onClick={() => start.mutate()} disabled={start.isPending}>{start.isPending ? t.piaStarting : t.piaBegin}</button>}
        {failure && <p className="tx-error" role="alert">{(failure.error as Error).message}</p>}
      </section>

      {needsConsent && <form className="card pia-card" onSubmit={submit} noValidate aria-labelledby="pia-consent">
        <h2 id="pia-consent">{t.piaConsentTitle}</h2>
        <div className="acct-field"><label htmlFor="pia-age">{t.piaAgeLabel}</label>
          <input id="pia-age" type="number" inputMode="numeric" min={13} max={120} value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} aria-invalid={Boolean(errors.age)} />
          {errors.age && <small className="acct-error" role="alert">{errors.age}</small>}</div>
        {Number.isInteger(age) && age >= 13 && age < 18 && <label className="pia-check"><input type="checkbox" checked={form.guardian} onChange={(e) => setForm({ ...form, guardian: e.target.checked })} />{t.piaGuardianLabel}</label>}
        {errors.guardian && <small className="acct-error" role="alert">{errors.guardian}</small>}
        <label className="pia-check"><input type="checkbox" checked={form.accepted} onChange={(e) => setForm({ ...form, accepted: e.target.checked })} />{t.piaAcceptLabel}</label>
        {errors.accepted && <small className="acct-error" role="alert">{errors.accepted}</small>}
        <button className="button button-primary" disabled={consent.isPending}>{consent.isPending ? t.piaStarting : t.piaConsentSubmit}</button>
      </form>}
    </div>
  </AppShell>
}
