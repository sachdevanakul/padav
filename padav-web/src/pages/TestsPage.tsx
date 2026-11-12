import { useState } from 'react'
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

type TestFilter = 'all' | 'available' | 'in-progress' | 'completed'

export default function TestsPage() {
  const language = preferencesStore((state) => state.language)
  const t = translations[language]
  const [filter, setFilter] = useState<TestFilter>('all')
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
  const completed = new Set((attempts.data ?? []).filter((attempt) => attempt.is_submitted).map((attempt) => attempt.test_id))
  const filteredTests = (tests.data ?? []).filter((test) => {
    if (filter === 'in-progress') return inProgress.has(test.id)
    if (filter === 'completed') return completed.has(test.id) && !inProgress.has(test.id)
    if (filter === 'available') return !completed.has(test.id) && !inProgress.has(test.id)
    return true
  })
  const filters: { id: TestFilter; label: string }[] = [
    { id: 'all', label: language === 'hi' ? 'सभी' : 'All tests' },
    { id: 'available', label: language === 'hi' ? 'उपलब्ध' : 'Available' },
    { id: 'in-progress', label: t.inProgress },
    { id: 'completed', label: t.submitted },
  ]

  return <AppShell>
    <section className="page-heading">
      <p className="eyebrow"><Trophy size={14} /> PADAV TEST ARENA</p>
      <h1>{t.testsTitle}</h1>
      <p className="muted">{t.testsSubtitle}</p>
    </section>

    {start.isError && <p className="tx-error" role="alert">{t.startFailed}</p>}

    {tests.isPending ? <div className="tx-test-grid" aria-busy="true" aria-label={t.loadingTests}>{[0, 1, 2].map((item) => <div key={item} className="phase6-skeleton" />)}</div>
      : tests.isError ? <div className="planner-state card" role="alert">{tests.error.message}</div>
      : tests.data.length === 0 ? <div className="planner-state card">{t.noTests}</div>
      : <>
        <div className="tx-test-filters" role="group" aria-label={language === 'hi' ? 'टेस्ट फ़िल्टर' : 'Filter tests'}>
          {filters.map((item) => <button key={item.id} type="button" aria-pressed={filter === item.id} onClick={() => setFilter(item.id)}>{item.label}</button>)}
        </div>
        {filteredTests.length === 0 ? <div className="empty-state card"><Trophy className="empty-icon" size={26} /><h2>{language === 'hi' ? 'कोई टेस्ट नहीं मिला' : 'No tests in this filter'}</h2><p>{language === 'hi' ? 'दूसरी स्थिति चुनें या बाद में फिर देखें।' : 'Choose another status or check back later.'}</p></div>
          : <section className="tx-test-grid" aria-label={t.testsTitle} aria-live="polite">
            {filteredTests.map((test, index) => <TestCard key={test.id} test={test} language={language} t={t} resume={inProgress.get(test.id)} isCompleted={completed.has(test.id)} starting={start.isPending && start.variables === test.id} onStart={() => start.mutate(test.id)} style={{ animationDelay: `${index * 45}ms` }} />)}
          </section>}
      </>}

    <section className="tx-attempts" aria-labelledby="attempts-heading">
      <h2 id="attempts-heading">{t.yourAttempts}</h2>
      {attempts.isPending ? <div className="tx-attempt-list" aria-busy="true">{[0, 1].map((item) => <div key={item} className="phase6-skeleton" />)}</div>
        : attempts.isError ? <div className="tx-error" role="alert">{attempts.error.message}</div>
        : attempts.data?.length === 0 ? <div className="empty-state card"><p>{t.noAttempts}</p></div>
        : <div className="tx-attempt-list card">
        {attempts.data?.map((attempt) => {
          const progress = attempt.total_questions ? Math.round(attempt.attempted_questions / attempt.total_questions * 100) : 0
          return <div className="tx-attempt-row" key={attempt.id}>
          <div><strong>{titleById.get(attempt.test_id) ?? attempt.test_title}</strong><small>{formatDateTime(attempt.started_at, language)}</small></div>
          <span className={`tx-pill ${attempt.is_submitted ? 'is-done' : 'is-live'}`}>{attempt.is_submitted ? t.submitted : t.inProgress}</span>
          {!attempt.is_submitted && <div className="tx-attempt-progress" role="progressbar" aria-label={language === 'hi' ? 'प्रश्न प्रगति' : 'Question progress'} aria-valuemin={0} aria-valuemax={attempt.total_questions} aria-valuenow={attempt.attempted_questions}><span><i style={{ width: `${progress}%` }} /></span><small>{attempt.attempted_questions}/{attempt.total_questions}</small></div>}
          <span className="tx-attempt-score">{attempt.is_submitted ? `${formatMarks(attempt.score_obtained)}/${formatMarks(attempt.max_score)}` : '—'}</span>
          <Link className="button button-secondary" to={attempt.is_submitted ? `/tests/attempts/${attempt.id}/result` : `/tests/attempts/${attempt.id}`}>{attempt.is_submitted ? t.viewResult : t.resumeTest}</Link>
        </div>})}
      </div>}
    </section>
  </AppShell>
}

function TestCard({ test, language, t, resume, isCompleted, starting, onStart, style }: { test: TestInfo; language: string; t: Record<string, string>; resume?: AttemptSummary; isCompleted: boolean; starting: boolean; onStart: () => void; style: React.CSSProperties }) {
  const description = pickText(language, test.description, test.description_hi)
  const status = resume ? t.inProgress : isCompleted ? t.submitted : (language === 'hi' ? 'उपलब्ध' : 'Available')
  return <article className="tx-test-card card phase6-enter" style={style}>
    <span className={`tx-status ${resume ? 'is-live' : isCompleted ? 'is-done' : ''}`}>{status}</span>
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
