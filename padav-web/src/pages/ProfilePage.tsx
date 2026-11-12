import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, Loader2, Trash2, UserRound } from 'lucide-react'
import AppShell from '../layouts/AppShell'
import { pickText } from '../lib/localize'
import { api, type ProfileUpdate } from '../services/api'
import { translations } from '../locales/translations'
import { authStore } from '../store/auth'
import { preferencesStore } from '../store/preferences'
import '../styles/account.css'

type Form = { fullName: string; phone: string; dob: string; education: string; goal: string }
type Errors = Partial<Record<keyof Form, string>>

const PHONE = /^\+?[0-9 ()\-]{7,20}$/
const EDUCATION = [['School', 'eduSchool'], ['Undergraduate', 'eduUndergrad'], ['Graduate', 'eduGraduate'], ['Postgraduate', 'eduPostgrad'], ['Working professional', 'eduWorking'], ['Other', 'eduOther']] as const

export function validateProfile(form: Form, t: Record<string, string>, today: Date = new Date()): Errors {
  const errors: Errors = {}
  const name = form.fullName.trim()
  if (name.length < 1 || name.length > 120) errors.fullName = t.errName
  if (form.phone.trim() && !PHONE.test(form.phone.trim())) errors.phone = t.errPhone
  if (form.dob) {
    const parsed = new Date(`${form.dob}T00:00:00`)
    if (Number.isNaN(parsed.getTime()) || parsed < new Date(1900, 0, 1) || parsed > today) errors.dob = t.errDob
  }
  if (form.goal.trim()) {
    const goal = Number(form.goal)
    if (!Number.isInteger(goal) || goal < 0 || goal > 168) errors.goal = t.errGoal
  }
  return errors
}

export default function ProfilePage() {
  const user = authStore((state) => state.user)
  const setUser = authStore((state) => state.setUser)
  const language = preferencesStore((state) => state.language)
  const t = translations[language]
  const queryClient = useQueryClient()
  const profile = useQuery({ queryKey: ['profile'], queryFn: api.profile, staleTime: 0 })
  const exams = useQuery({ queryKey: ['exams'], queryFn: api.exams })
  const mine = useQuery({ queryKey: ['my-exams'], queryFn: api.myExams, staleTime: 0 })
  const [form, setForm] = useState<Form | null>(null)
  const [errors, setErrors] = useState<Errors>({})
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (profile.data && user && !form) {
      setForm({
        fullName: user.full_name ?? '', phone: profile.data.phone ?? '', dob: profile.data.date_of_birth ?? '',
        education: profile.data.education_level ?? '', goal: profile.data.study_goal_hours_per_week?.toString() ?? '',
      })
    }
  }, [profile.data, user, form])

  const save = useMutation({
    mutationFn: async (values: Form) => {
      const body: ProfileUpdate = {
        phone: values.phone.trim() || null, date_of_birth: values.dob || null,
        education_level: values.education || null, study_goal_hours_per_week: values.goal.trim() ? Number(values.goal) : null,
      }
      await api.updateProfile(body)
      if (values.fullName.trim() !== (user?.full_name ?? '')) setUser(await api.updateMe({ full_name: values.fullName.trim() }))
    },
    onSuccess: async () => { setSaved(true); await queryClient.invalidateQueries({ queryKey: ['profile'] }) },
  })
  const remove = useMutation({ mutationFn: api.removeExam, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['my-exams'] }) })

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!form) return
    setSaved(false)
    const found = validateProfile(form, t)
    setErrors(found)
    if (Object.keys(found).length === 0) save.mutate(form)
  }
  const set = (key: keyof Form) => (value: string) => { setSaved(false); setForm((prev) => (prev ? { ...prev, [key]: value } : prev)) }
  const examName = (id: string) => { const exam = exams.data?.find((item) => item.id === id); return exam ? pickText(language, exam.name, exam.name_hi) : id }
  const since = user?.created_at ? new Intl.DateTimeFormat(language === 'hi' ? 'hi-IN' : 'en-IN', { month: 'long', year: 'numeric' }).format(new Date(user.created_at.endsWith('Z') ? user.created_at : `${user.created_at}Z`)) : ''

  return <AppShell>
    <section className="page-heading"><p className="eyebrow"><UserRound size={14} /> PADAV PROFILE</p><h1>{t.profileTitle}</h1><p className="muted">{t.profileSubtitle}</p></section>
    {profile.isError ? <div className="planner-state card" role="alert">{t.loadFailed}</div> : !form ? <div className="planner-state card"><Loader2 className="tx-spin" size={18} /></div> : <div className="acct-grid">
      <form className="acct-card card" onSubmit={submit} noValidate aria-labelledby="personal-heading">
        <div className="acct-identity"><span className="avatar acct-avatar" aria-hidden="true">{(user?.full_name || user?.email || 'P').slice(0, 1).toUpperCase()}</span><div><strong>{user?.full_name || user?.email}</strong><small>{user?.email}{since && ` · ${t.memberSince} ${since}`}</small></div></div>
        <h2 id="personal-heading">{t.personalDetails}</h2>
        <Field id="pf-name" label={t.fullNameLabel} error={errors.fullName}><input id="pf-name" value={form.fullName} maxLength={120} autoComplete="name" onChange={(e) => set('fullName')(e.target.value)} aria-invalid={Boolean(errors.fullName)} /></Field>
        <div className="acct-row">
          <Field id="pf-phone" label={t.phoneLabel} error={errors.phone}><input id="pf-phone" type="tel" value={form.phone} maxLength={20} autoComplete="tel" onChange={(e) => set('phone')(e.target.value)} aria-invalid={Boolean(errors.phone)} /></Field>
          <Field id="pf-dob" label={t.dobLabel} error={errors.dob}><input id="pf-dob" type="date" value={form.dob} onChange={(e) => set('dob')(e.target.value)} aria-invalid={Boolean(errors.dob)} /></Field>
        </div>
        <div className="acct-row">
          <Field id="pf-edu" label={t.educationLabel}><select id="pf-edu" value={form.education} onChange={(e) => set('education')(e.target.value)}>
            <option value="">{t.notSet}</option>
            {EDUCATION.map(([value, key]) => <option key={value} value={value}>{t[key]}</option>)}
            {form.education && !EDUCATION.some(([value]) => value === form.education) && <option value={form.education}>{form.education}</option>}
          </select></Field>
          <Field id="pf-goal" label={t.goalLabel} error={errors.goal}><input id="pf-goal" type="number" inputMode="numeric" min={0} max={168} value={form.goal} onChange={(e) => set('goal')(e.target.value)} aria-invalid={Boolean(errors.goal)} /></Field>
        </div>
        {save.isError && <p className="tx-error" role="alert">{(save.error as Error).message}</p>}
        <div className="acct-actions">
          <button className="button button-primary" disabled={save.isPending}>{save.isPending ? t.savingChanges : t.saveChanges}</button>
          {saved && <span className="acct-ok" role="status"><Check size={14} />{t.savedOk}</span>}
        </div>
      </form>

      <section className="acct-card card" aria-labelledby="exams-heading">
        <h2 id="exams-heading">{t.myExamsTitle}</h2>
        {mine.isPending ? null : mine.data?.length ? <ul className="acct-list">
          {mine.data.map((item) => <li key={item.id}><span>{examName(item.exam_id)}{item.is_primary && <small className="tx-pill is-done">{t.primaryLabel}</small>}</span>
            <button className="button button-ghost" onClick={() => remove.mutate(item.exam_id)} disabled={remove.isPending} aria-label={`${t.removeLabel} ${examName(item.exam_id)}`}><Trash2 size={14} />{t.removeLabel}</button></li>)}
        </ul> : <p className="muted">{t.noExamsYet}</p>}
        <Link className="button button-secondary" to="/exams">{t.manageExams}</Link>
      </section>
    </div>}
  </AppShell>
}

function Field({ id, label, error, children }: { id: string; label: string; error?: string; children: React.ReactNode }) {
  return <div className="acct-field"><label htmlFor={id}>{label}</label>{children}{error && <small className="acct-error" role="alert">{error}</small>}</div>
}
