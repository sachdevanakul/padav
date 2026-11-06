import { useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, ArrowRight, CalendarDays, Check, Clock3, Plus, Trash2, X } from 'lucide-react'
import AppShell from '../layouts/AppShell'
import { api, type PlannerBlock } from '../services/api'
import { preferencesStore } from '../store/preferences'
import { translations } from '../locales/translations'

function dateKey(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
function weekStart(anchor: Date) {
  const start = new Date(anchor.getFullYear(), anchor.getMonth(), anchor.getDate())
  start.setDate(start.getDate() - ((start.getDay() + 6) % 7))
  return start
}
function weekDates(start: Date) {
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(start)
    date.setDate(start.getDate() + index)
    return date
  })
}
function formatTime(value: string, language: string) {
  const [hours, minutes] = value.split(':').map(Number)
  return new Intl.DateTimeFormat(language === 'hi' ? 'hi-IN' : 'en-IN', { hour: 'numeric', minute: '2-digit' }).format(new Date(2000, 0, 1, hours, minutes))
}

export default function PlannerPage() {
  const language = preferencesStore((state) => state.language)
  const t = translations[language]
  const queryClient = useQueryClient()
  const [anchor, setAnchor] = useState(() => new Date())
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')
  const week = useMemo(() => weekDates(weekStart(anchor)), [anchor])
  const start = dateKey(week[0])
  const end = dateKey(week[6])
  const plannerKey = ['planner', start, end]
  const query = useQuery({ queryKey: plannerKey, queryFn: () => api.planner(start, end) })
  const add = useMutation({
    mutationFn: api.addPlannerBlock,
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['planner'] }); setShowForm(false); setError('') },
    onError: (cause: Error) => setError(cause.message.includes('overlap') ? t.overlap : cause.message),
  })
  const complete = useMutation({
    mutationFn: ({ id, value }: { id: string; value: boolean }) => api.completePlannerBlock(id, value),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['planner'] }),
  })
  const remove = useMutation({ mutationFn: api.deletePlannerBlock, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['planner'] }) })
  const blocks = query.data ?? []
  const completedCount = blocks.filter((block) => block.completed).length
  const dateLocale = language === 'hi' ? 'hi-IN' : 'en-IN'
  const weekLabel = `${new Intl.DateTimeFormat(dateLocale, { month: 'short', day: 'numeric' }).format(week[0])} – ${new Intl.DateTimeFormat(dateLocale, { month: 'short', day: 'numeric', year: 'numeric' }).format(week[6])}`

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const title = String(form.get('title') || '').trim()
    const subject = String(form.get('subject') || '').trim()
    const study_date = String(form.get('study_date') || '')
    const start_time = String(form.get('start_time') || '')
    const end_time = String(form.get('end_time') || '')
    setError('')
    if (end_time <= start_time) { setError(language === 'hi' ? 'समाप्ति का समय, शुरू होने के समय के बाद होना चाहिए।' : 'End time must be after start time.'); return }
    await add.mutateAsync({ title, subject: subject || null, study_date, start_time, end_time })
  }

  return <AppShell>
    <section className="planner-heading">
      <div><p className="eyebrow"><CalendarDays size={14} /> PADAV PLANNER</p><h1>{t.plannerTitle}</h1><p className="muted">{t.plannerSubtitle}</p></div>
      <button className="button button-primary" onClick={() => { setShowForm(true); setError('') }}><Plus size={16} />{t.addSession}</button>
    </section>

    <section className="planner-summary card">
      <div className="planner-week-nav"><button className="icon-button" aria-label={t.previousWeek} onClick={() => setAnchor((value) => new Date(value.getFullYear(), value.getMonth(), value.getDate() - 7))}><ArrowLeft size={16} /></button><div><span>{t.thisWeek}</span><strong>{weekLabel}</strong></div><button className="icon-button" aria-label={t.nextWeek} onClick={() => setAnchor((value) => new Date(value.getFullYear(), value.getMonth(), value.getDate() + 7))}><ArrowRight size={16} /></button><button className="planner-today" onClick={() => setAnchor(new Date())}>{language === 'hi' ? 'आज' : 'Today'}</button></div>
      <div className="planner-progress"><span className="planner-progress-icon"><Check size={15} /></span><strong>{completedCount}/{blocks.length}</strong><span>{language === 'hi' ? 'सत्र पूरे' : 'sessions complete'}</span><div><i style={{ width: `${blocks.length ? completedCount / blocks.length * 100 : 0}%` }} /></div></div>
    </section>

    {query.isPending ? <div className="planner-state card">{language === 'hi' ? 'आपकी समय-सारणी लोड हो रही है…' : 'Loading your timetable…'}</div> : query.isError ? <div className="planner-state card">{query.error.message}</div> : <section className="planner-week" aria-label={t.plannerTitle}>
      {week.map((day) => {
        const dayBlocks = blocks.filter((block) => block.study_date === dateKey(day))
        const isToday = dateKey(day) === dateKey(new Date())
        return <article className={`planner-day card ${isToday ? 'planner-day-today' : ''}`} key={dateKey(day)}>
          <header className="planner-day-head"><div><span>{new Intl.DateTimeFormat(dateLocale, { weekday: 'short' }).format(day)}</span><strong>{new Intl.DateTimeFormat(dateLocale, { day: 'numeric', month: 'short' }).format(day)}</strong></div>{isToday && <i />}</header>
          <div className="planner-day-sessions">
            {dayBlocks.length === 0 ? <button className="planner-empty" onClick={() => setShowForm(true)}><Plus size={15} /><span>{t.noSessions}</span><small>{t.noSessionsHint}</small></button> : dayBlocks.map((block) => <PlannerSession key={block.id} block={block} language={language} t={t} onComplete={(value) => complete.mutate({ id: block.id, value })} onDelete={() => remove.mutate(block.id)} />)}
          </div>
          {dayBlocks.length > 0 && <button className="planner-add-day" onClick={() => setShowForm(true)}><Plus size={13} /> {t.addSession}</button>}
        </article>
      })}
    </section>}

    {showForm && <div className="planner-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setShowForm(false) }}><section className="planner-modal card" role="dialog" aria-modal="true" aria-labelledby="planner-form-title"><header><div><p className="eyebrow"><Clock3 size={14} /> {t.thisWeek}</p><h2 id="planner-form-title">{t.addSession}</h2></div><button className="icon-button" aria-label={t.cancel} onClick={() => setShowForm(false)}><X size={17} /></button></header>
      <form onSubmit={submit}><label>{t.sessionTitle}<input name="title" required maxLength={120} placeholder={language === 'hi' ? 'जैसे: गणित अभ्यास' : 'e.g. Quantitative aptitude practice'} autoFocus /></label><label>{t.subject}<input name="subject" maxLength={80} placeholder={language === 'hi' ? 'जैसे: गणित' : 'e.g. Quantitative aptitude'} /></label><label>{t.date}<select name="study_date" defaultValue={dateKey(week.find((day) => dateKey(day) === dateKey(new Date())) ?? week[0])}>{week.map((day) => <option key={dateKey(day)} value={dateKey(day)}>{new Intl.DateTimeFormat(dateLocale, { weekday: 'long', month: 'short', day: 'numeric' }).format(day)}</option>)}</select></label><div className="planner-time-fields"><label>{t.startTime}<input name="start_time" type="time" defaultValue="09:00" required /></label><label>{t.endTime}<input name="end_time" type="time" defaultValue="10:00" required /></label></div>{error && <p className="planner-error" role="alert">{error}</p>}<footer><button className="button button-ghost" type="button" onClick={() => setShowForm(false)}>{t.cancel}</button><button className="button button-primary" type="submit" disabled={add.isPending}>{add.isPending ? (language === 'hi' ? 'जोड़ रहे हैं…' : 'Adding…') : t.saveSession}</button></footer></form>
    </section></div>}
  </AppShell>
}

function PlannerSession({ block, language, t, onComplete, onDelete }: { block: PlannerBlock; language: string; t: Record<string, string>; onComplete: (value: boolean) => void; onDelete: () => void }) {
  return <div className={`planner-session ${block.completed ? 'is-complete' : ''}`}><div className="planner-session-time">{formatTime(block.start_time, language)}<span>–</span>{formatTime(block.end_time, language)}</div><strong>{block.title}</strong>{block.subject && <span className="planner-subject">{block.subject}</span>}<div className="planner-session-actions"><button aria-label={block.completed ? t.completed : t.complete} title={block.completed ? t.completed : t.complete} onClick={() => onComplete(!block.completed)} className={block.completed ? 'planner-check checked' : 'planner-check'}>{block.completed ? <Check size={13} /> : <span />}</button><small>{block.completed ? t.completed : t.planned}</small><button aria-label={t.delete} title={t.delete} onClick={onDelete} className="planner-delete"><Trash2 size={13} /></button></div></div>
}
