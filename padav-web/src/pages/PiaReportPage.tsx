import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Loader2, ShieldCheck } from 'lucide-react'
import AppShell from '../layouts/AppShell'
import { api } from '../services/api'
import { translations } from '../locales/translations'
import { preferencesStore } from '../store/preferences'
import '../styles/pia.css'

export default function PiaReportPage() {
  const { sessionId = '' } = useParams()
  const t = translations[preferencesStore((state) => state.language)]
  const report = useQuery({ queryKey: ['pia-report', sessionId], queryFn: () => api.piaReport(sessionId) })
  if (report.isError) return <AppShell><div className="planner-state card" role="alert">{t.piaLoadFailed} <Link to={`/pia/sessions/${sessionId}`}>{t.piaBackToAssessment}</Link></div></AppShell>
  if (!report.data) return <AppShell><div className="planner-state card"><Loader2 className="tx-spin" size={18} /></div></AppShell>
  const r = report.data
  const percent = (value: number) => `${Math.round(value * 100)}%`
  // Deliberately no IQ, percentile or label: only raw counts, until validated norms exist.
  return <AppShell>
    <section className="page-heading"><p className="eyebrow">PIA · {r.form_code} v{r.form_version}</p><h1>{t.piaReportTitle}</h1></section>
    <p className="pia-banner" role="note"><ShieldCheck size={16} />{t.piaExperimental}</p>
    <div className="pia-summary">
      <div className="card pia-stat"><small>{t.piaRawScore}</small><strong>{r.total_correct} / {r.total_questions}</strong></div>
      <div className="card pia-stat"><small>{t.piaRawAccuracy}</small><strong>{percent(r.raw_accuracy)}</strong></div>
    </div>
    <p className="muted">{t.piaAccuracyNote}</p>
    <section className="card pia-card" aria-labelledby="pia-domains">
      <h2 id="pia-domains">{t.piaByDomain}</h2>
      <ul className="pia-domains">
        {r.domains.map((d) => <li key={d.domain}>
          <div className="pia-domain-head"><strong>{t[`piaDomain_${d.domain}`] ?? d.label}</strong><span>{d.correct}/{d.questions} {t.piaCorrect}{d.omitted > 0 && ` · ${d.omitted} ${t.piaOmitted}`}</span></div>
          <div className="pia-bar" role="img" aria-label={`${percent(d.accuracy)}`}><i style={{ width: percent(d.accuracy) }} /></div>
          {(d.timed_out || d.interrupted) && <div className="pia-flags">{d.timed_out && <span className="tx-pill is-timed_out">{t.piaTimedOut}</span>}{d.interrupted && <span className="tx-pill is-live">{t.piaInterrupted}</span>}</div>}
        </li>)}
      </ul>
    </section>
    <section className="card pia-card" aria-labelledby="pia-notices">
      <h2 id="pia-notices">{t.piaNotices}</h2>
      <ul className="pia-rules">{r.notices.map((notice) => <li key={notice}>{notice}</li>)}</ul>
    </section>
    <Link className="button button-secondary" to="/pia">{t.piaBackToAssessment}</Link>
  </AppShell>
}
