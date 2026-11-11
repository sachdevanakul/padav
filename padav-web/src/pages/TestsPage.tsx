import { useMutation, useQuery } from '@tanstack/react-query'
import { Clock3, ListChecks, MinusCircle, Play, RotateCcw, Trophy } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import AppShell from '../layouts/AppShell'
import { formatDateTime } from '../lib/dates'
import { formatMarks, pickText } from '../lib/localize'
import { api, type AttemptSummary, type TestInfo } from '../services/api'
import { translations } from '../locales/translations'
import { preferencesStore } from '../store/preferences'
import '../styles/tests.css'

export default function TestsPage() {
  const language = preferencesStore((state) => state.language)
  const t = translations[language]
  const navigate = useNavigate()
  const tests = useQuery({ queryKey: ['tests'], queryFn: api.tests })
  const attempts = useQuery({ queryKey: ['attempts'], queryFn: api.attempts, staleTime: 0 })
  const start = useMutation({
    mutationFn: api.startTest,
    onSuccess: (started) => navigate(`/tests/attempts/${started.attempt_id}`),
  })

  const titleById = new Map((tests.data ?? []).map((test) => [test.id, pickText(language, test.title, test.title_hi)]))
  const inProgress = new Map<string, AttemptSummary>()
  for (const attempt of attempts.data ?? []) if (!attempt.is_submitted && !inProgress.has(attempt.test_id)) inProgress.set(attempt.test_id, attempt)

  return <AppShell>
    <section className="page-heading">
      <p className="eyebrow"><Trophy size={14} /> PADAV TEST ARENA</p>
      <h1>{t.testsTitle}</h1>
      <p className="muted">{t.testsSubtitle}</p>
    </section>

    {start.isError && <p className="tx-error" role="alert">{t.startFailed}</p>}

    {tests.isPending ? <div className="planner-state card">{t.loadingTests}</div>
      : tests.isError ? <div className="planner-state card" role="alert">{tests.error.message}</div>
      : tests.data.length === 0 ? <div className="planner-state card">{t.noTests}</div>
      : <section className="tx-test-grid" aria-label={t.testsTitle}>
        {tests.data.map((test) => <TestCard key={test.id} test={test} language={language} t={t} resume={inProgress.get(test.id)} starting={start.isPending && start.variables === test.id} onStart={() => start.mutate(test.id)} />)}
      </section>}

    <section className="tx-attempts" aria-labelledby="attempts-heading">
      <h2 id="attempts-heading">{t.yourAttempts}</h2>
      {attempts.isPending ? null : attempts.data?.length === 0 ? <p className="muted">{t.noAttempts}</p> : <div className="tx-attempt-list card">
        {attempts.data?.map((attempt) => <div className="tx-attempt-row" key={attempt.id}>
          <div><strong>{titleById.get(attempt.test_id) ?? attempt.test_title}</strong><small>{formatDateTime(attempt.started_at, language)}</small></div>
          <span className={`tx-pill ${attempt.is_submitted ? 'is-done' : 'is-live'}`}>{attempt.is_submitted ? t.submitted : t.inProgress}</span>
          <span className="tx-attempt-score">{attempt.is_submitted ? `${formatMarks(attempt.score_obtained)}/${formatMarks(attempt.max_score)}` : '—'}</span>
          <Link className="button button-secondary" to={attempt.is_submitted ? `/tests/attempts/${attempt.id}/result` : `/tests/attempts/${attempt.id}`}>{attempt.is_submitted ? t.viewResult : t.resumeTest}</Link>
        </div>)}
      </div>}
    </section>
  </AppShell>
}

function TestCard({ test, language, t, resume, starting, onStart }: { test: TestInfo; language: string; t: Record<string, string>; resume?: AttemptSummary; starting: boolean; onStart: () => void }) {
  const description = pickText(language, test.description, test.description_hi)
  return <article className="tx-test-card card">
    <h3>{pickText(language, test.title, test.title_hi)}</h3>
    {description && <p className="muted">{description}</p>}
    <ul className="tx-chips">
      <li><ListChecks size={14} />{test.total_questions} {t.questionsCount}</li>
      <li><Clock3 size={14} />{test.duration_minutes} {t.minutes}</li>
      <li><Trophy size={14} />{formatMarks(test.total_marks)} {t.marksLabel}</li>
      {test.negative_marks_per_question > 0 && <li><MinusCircle size={14} />−{formatMarks(test.negative_marks_per_question)} {t.negativeMarking}</li>}
    </ul>
    {resume
      ? <Link className="button button-primary" to={`/tests/attempts/${resume.id}`}><RotateCcw size={15} />{t.resumeTest}</Link>
      : <button className="button button-primary" onClick={onStart} disabled={starting}><Play size={15} />{t.startTest}</button>}
  </article>
}
