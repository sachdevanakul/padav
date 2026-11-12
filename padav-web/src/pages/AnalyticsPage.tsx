import { useMemo, useState, type ReactNode } from 'react'
import { Activity, ArrowRight, BookOpen, Clock3, Flame, Target, Trophy } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import AppShell from '../layouts/AppShell'
import { formatDateTime } from '../lib/dates'
import { formatMarks } from '../lib/localize'
import { api } from '../services/api'
import { preferencesStore } from '../store/preferences'
import { translations } from '../locales/translations'
import { AreaChart, BarChart, CircularProgress, DonutChart, LineChart } from '../components/charts'
import '../styles/account.css'

const DATE_RANGES = [
  { key: '7d', label: '7 days' },
  { key: '30d', label: '30 days' },
  { key: '90d', label: '90 days' },
] as const

function formatDateKey(language: string, date: string): string {
  return new Intl.DateTimeFormat(language === 'hi' ? 'hi-IN' : 'en-IN', {
    month: 'short',
    day: 'numeric',
  }).format(new Date(date))
}

export default function AnalyticsPage() {
  const language = preferencesStore((state) => state.language)
  const t = translations[language]
  const [dateRange, setDateRange] = useState<(typeof DATE_RANGES)[number]['key']>('30d')
  const overviewQuery = useQuery({ queryKey: ['overview'], queryFn: api.overview })
  const trendsQuery = useQuery({ queryKey: ['trends'], queryFn: api.trends })
  const attemptsQuery = useQuery({ queryKey: ['attempts'], queryFn: api.attempts })
  const loading = overviewQuery.isPending || trendsQuery.isPending || attemptsQuery.isPending
  const overview = overviewQuery.data
  const attempts = attemptsQuery.data ?? []

  const cutoff = useMemo(() => {
    const days = Number.parseInt(dateRange, 10)
    return new Date(Date.now() - days * 24 * 60 * 60 * 1000)
  }, [dateRange])
  const filteredTrends = useMemo(
    () => (trendsQuery.data ?? []).filter((point) => new Date(point.date) >= cutoff),
    [trendsQuery.data, cutoff],
  )
  const filteredAttempts = useMemo(
    () => attempts.filter((attempt) => new Date(attempt.started_at) >= cutoff),
    [attempts, cutoff],
  )

  const accuracyData = useMemo(
    () => filteredTrends.map((point) => ({
      date: formatDateKey(language, point.date),
      score: Math.round(point.accuracy),
      accuracy: Math.round(point.accuracy),
      questions_attempted: point.questions_attempted,
    })),
    [filteredTrends, language],
  )
  const scoreData = useMemo(
    () => filteredTrends.map((point) => ({
      date: formatDateKey(language, point.date),
      score: Math.round(point.score),
      accuracy: Math.round(point.accuracy),
      questions_attempted: point.questions_attempted,
    })),
    [filteredTrends, language],
  )
  const questionsData = useMemo(
    () => filteredTrends.map((point) => ({
      name: formatDateKey(language, point.date),
      value: point.questions_attempted,
    })),
    [filteredTrends, language],
  )
  const testAccuracy = useMemo(() => {
    const byTest = new Map<string, { correct: number; total: number }>()
    for (const attempt of filteredAttempts) {
      if (!attempt.is_submitted) continue
      const current = byTest.get(attempt.test_title) ?? { correct: 0, total: 0 }
      current.correct += attempt.correct_answers
      current.total += attempt.total_questions
      byTest.set(attempt.test_title, current)
    }
    return Array.from(byTest, ([name, result]) => ({
      name,
      value: result.total ? Math.round((result.correct / result.total) * 100) : 0,
    }))
  }, [filteredAttempts])
  const completionSegments = useMemo(() => {
    const completed = filteredAttempts.filter((attempt) => attempt.is_submitted).length
    const inProgress = filteredAttempts.length - completed
    return filteredAttempts.length
      ? [
          { name: t.submitted, value: completed, color: 'mint' as const },
          { name: t.inProgress, value: inProgress, color: 'blue' as const },
        ]
      : []
  }, [filteredAttempts, t.inProgress, t.submitted])
  const recentAttempts = useMemo(
    () => [...attempts].sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime()).slice(0, 5),
    [attempts],
  )
  const error = overviewQuery.error ?? trendsQuery.error ?? attemptsQuery.error

  return <AppShell>
    <section className="page-heading phase6-enter">
      <p className="eyebrow"><Activity size={14} /> PADAV ANALYTICS</p>
      <h1>Learning analytics</h1>
      <p className="muted">Track your progress with the results of your practice.</p>
    </section>

    {error && <div className="tx-error" role="alert">
      {error.message}
      <button className="tx-link" onClick={() => { void overviewQuery.refetch(); void trendsQuery.refetch(); void attemptsQuery.refetch() }}>Try again</button>
    </div>}

    <div className="analytics-range" role="group" aria-label="Analytics date range">
      {DATE_RANGES.map((range) => <button key={range.key} type="button" aria-pressed={dateRange === range.key} onClick={() => setDateRange(range.key)}>{range.label}</button>)}
    </div>

    <section className="analytics-metrics" aria-label="Learning overview" aria-busy={loading}>
      <Metric icon={<Target size={17} />} label={t.accuracy} value={overview ? `${Math.round(overview.overall_accuracy)}%` : '—'} delay={0} />
      <Metric icon={<BookOpen size={17} />} label={t.questions} value={overview?.total_questions_attempted ?? '—'} delay={60} />
      <Metric icon={<Clock3 size={17} />} label={t.hours} value={overview ? `${overview.total_study_hours}h` : '—'} delay={120} />
      <Metric icon={<Flame size={17} />} label={t.streak} value={overview?.current_streak ?? '—'} delay={180} />
    </section>

    <section className="analytics-charts" aria-label="Performance charts">
      <AreaChart data={accuracyData} title="Accuracy over time" subtitle="Actual test accuracy" colorKey="mint" loading={trendsQuery.isPending} emptyMessage="No accuracy data in this period." />
      <LineChart data={scoreData} title="Score trend" subtitle="Scores from your attempts" colorKey="primary" loading={trendsQuery.isPending} emptyMessage="No score data in this period." />
      <BarChart data={questionsData} title="Questions attempted" subtitle="Daily question count" colorKey="blue" loading={trendsQuery.isPending} emptyMessage="No question activity in this period." />
      <CircularProgress title="Overall accuracy" subtitle="Across all attempts" value={overview?.overall_accuracy ?? 0} label="accuracy" colorKey="mint" loading={overviewQuery.isPending} />
      <DonutChart data={completionSegments} title="Attempt status" subtitle="For the selected period" centerLabel="attempts" centerValue={filteredAttempts.length} loading={attemptsQuery.isPending} emptyMessage="No attempts in this period." />
      <BarChart data={testAccuracy} title="Accuracy by test" subtitle="Based on your attempts" colorKey="purple" loading={attemptsQuery.isPending} emptyMessage="No test results in this period." />
    </section>

    <section className="analytics-recent" aria-labelledby="analytics-recent-heading">
      <div className="section-heading">
        <div><p className="eyebrow">KEEP YOUR MOMENTUM</p><h2 id="analytics-recent-heading">Recent attempts</h2></div>
        <Link className="text-link" to="/tests">{t.yourAttempts} <ArrowRight size={14} /></Link>
      </div>
      {attemptsQuery.isPending ? <div className="analytics-recent-list" aria-busy="true">{[0, 1, 2].map((item) => <div key={item} className="phase6-skeleton" />)}</div>
        : recentAttempts.length === 0 ? <div className="empty-state card"><Trophy className="empty-icon" size={26} /><h2>No attempts yet</h2><p>Complete a practice test to see your progress here.</p><Link className="button button-secondary" to="/tests">Browse tests</Link></div>
        : <div className="analytics-recent-list card">{recentAttempts.map((attempt) => <Link className="analytics-attempt" key={attempt.id} to={attempt.is_submitted ? `/tests/attempts/${attempt.id}/result` : `/tests/attempts/${attempt.id}`}>
          <span className="analytics-attempt-icon"><Trophy size={16} /></span>
          <span className="analytics-attempt-copy"><strong>{attempt.test_title}</strong><small>{formatDateTime(attempt.started_at, language)}</small></span>
          <span className={`tx-pill ${attempt.is_submitted ? 'is-done' : 'is-live'}`}>{attempt.is_submitted ? t.submitted : t.inProgress}</span>
          <strong className="analytics-attempt-score">{attempt.is_submitted ? `${formatMarks(attempt.score_obtained)} / ${formatMarks(attempt.max_score)}` : `${attempt.attempted_questions}/${attempt.total_questions}`}</strong>
          <ArrowRight size={15} />
        </Link>)}</div>}
    </section>
  </AppShell>
}

function Metric({ icon, label, value, delay }: { icon: ReactNode; label: string; value: string | number; delay: number }) {
  return <article className="analytics-metric card phase6-enter" style={{ animationDelay: `${delay}ms` }}>
    <span className="analytics-metric-icon">{icon}</span>
    <span className="analytics-metric-label">{label}</span>
    <strong>{value}</strong>
  </article>
}
