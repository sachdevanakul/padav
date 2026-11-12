import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, Clock3, Loader2, Lock, Play } from 'lucide-react'
import AppShell from '../layouts/AppShell'
import { PiaRunner } from '../components/pia/PiaRunner'
import { api } from '../services/api'
import { translations } from '../locales/translations'
import { preferencesStore } from '../store/preferences'
import '../styles/pia.css'

export default function PiaSessionPage() {
  const { sessionId = '' } = useParams()
  const t = translations[preferencesStore((state) => state.language)]
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  // Always fetched fresh: the countdown must start from the server's current seconds_remaining.
  const session = useQuery({ queryKey: ['pia-session', sessionId], queryFn: () => api.piaSession(sessionId), staleTime: 0, gcTime: 0, refetchOnMount: 'always' })
  const [error, setError] = useState('')

  const start = useMutation({
    mutationFn: (domain: string) => api.piaStartSubtest(sessionId, domain),
    onSuccess: async (items, domain) => {
      queryClient.setQueryData(['pia-items', sessionId, domain], items)
      await queryClient.invalidateQueries({ queryKey: ['pia-session', sessionId] })
    },
    onError: (e) => setError((e as Error).message),
  })
  const finish = useMutation({
    mutationFn: () => api.piaFinish(sessionId),
    onSuccess: () => navigate(`/pia/sessions/${sessionId}/report`, { replace: true }),
    onError: (e) => setError((e as Error).message),
  })

  if (session.isError) return <AppShell><div className="planner-state card" role="alert">{t.piaLoadFailed} <Link to="/pia">{t.piaBackToAssessment}</Link></div></AppShell>
  if (!session.data) return <AppShell><div className="planner-state card"><Loader2 className="tx-spin" size={18} /></div></AppShell>

  const data = session.data
  if (data.status === 'completed') return <AppShell><div className="card pia-card"><Link className="button button-primary" to={`/pia/sessions/${sessionId}/report`}>{t.piaFinish}</Link></div></AppShell>
  const running = data.runs.find((run) => run.status === 'in_progress')
  if (running) return <PiaRunner key={running.domain} sessionId={sessionId} run={running} onDone={() => void session.refetch()} />

  const next = data.runs.find((run) => run.status === 'pending')
  const done = data.runs.filter((run) => run.status === 'completed' || run.status === 'timed_out').length
  return <AppShell>
    <section className="page-heading"><p className="eyebrow">PIA</p><h1>{t.piaTitle}</h1><p className="muted">{done}/{data.runs.length} {t.piaSections.toLowerCase()}</p></section>
    <p className="pia-banner" role="note">{t.piaExperimental}</p>
    <ol className="pia-sections">
      {data.runs.map((run) => {
        const isNext = run === next
        return <li key={run.domain} className={`card pia-section is-${run.status}`}>
          <span className="pia-section-icon" aria-hidden="true">{run.status === 'completed' ? <Check size={16} /> : run.status === 'timed_out' ? <Clock3 size={16} /> : isNext ? <Play size={16} /> : <Lock size={16} />}</span>
          <div className="pia-section-text">
            <h2>{run.sequence}. {t[`piaDomain_${run.domain}`] ?? run.label}</h2>
            <p className="muted">{t[`piaConstruct_${run.domain}`] ?? run.description}</p>
            <small>{run.question_count} {t.questionsCount} · {Math.round(run.time_limit_seconds / 60)} {t.minutes}</small>
          </div>
          {isNext ? <div className="pia-section-action"><button className="button button-primary" onClick={() => { setError(''); start.mutate(run.domain) }} disabled={start.isPending}>{t.piaStartSection}</button><small className="muted">{t.piaReadyNote}</small></div>
            : <span className={`tx-pill is-${run.status}`}>{t[`piaStatus_${run.status}`]}</span>}
        </li>
      })}
    </ol>
    {error && <p className="tx-error" role="alert">{error}</p>}
    {!next && <button className="button button-primary pia-finish" onClick={() => finish.mutate()} disabled={finish.isPending}>{finish.isPending ? t.piaFinishing : t.piaFinish}</button>}
  </AppShell>
}
