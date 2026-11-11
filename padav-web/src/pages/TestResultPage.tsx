import { useState } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Check, X } from 'lucide-react'
import AppShell from '../layouts/AppShell'
import { formatMarks, pickText } from '../lib/localize'
import { api, type ReviewItem } from '../services/api'
import { translations } from '../locales/translations'
import { preferencesStore } from '../store/preferences'
import '../styles/tests.css'

type Filter = 'all' | 'correct' | 'incorrect' | 'unanswered'

function outcome(item: ReviewItem): Exclude<Filter, 'all'> {
  if (item.selected_option_key === null) return 'unanswered'
  return item.selected_option_key === item.correct_option_key ? 'correct' : 'incorrect'
}

export default function TestResultPage() {
  const { attemptId = '' } = useParams()
  const language = preferencesStore((state) => state.language)
  const t = translations[language]
  const [filter, setFilter] = useState<Filter>('all')
  const attempt = useQuery({ queryKey: ['attempt', attemptId, 'result'], queryFn: () => api.attempt(attemptId), staleTime: 0 })
  const review = useQuery({ queryKey: ['attempt-review', attemptId], queryFn: () => api.attemptReview(attemptId), enabled: attempt.data?.is_submitted === true })

  if (attempt.data && !attempt.data.is_submitted) return <Navigate to={`/tests/attempts/${attemptId}`} replace />
  if (attempt.isError) return <AppShell><div className="planner-state card" role="alert">{attempt.error.message}</div></AppShell>
  if (!attempt.data) return <AppShell><div className="planner-state card">{t.loadingResult}</div></AppShell>

  const a = attempt.data
  const items = review.data ?? []
  const counts = { correct: 0, incorrect: 0, unanswered: 0 }
  for (const item of items) counts[outcome(item)] += 1
  const visible = items.map((item, number) => ({ item, number })).filter(({ item }) => filter === 'all' || outcome(item) === filter)
  const filters: { id: Filter; label: string; count: number }[] = [
    { id: 'all', label: t.filterAll, count: items.length },
    { id: 'correct', label: t.correctLabel, count: counts.correct },
    { id: 'incorrect', label: t.incorrectLabel, count: counts.incorrect },
    { id: 'unanswered', label: t.unansweredLabel, count: counts.unanswered },
  ]

  return <AppShell>
    <section className="page-heading"><p className="eyebrow">PADAV RESULT</p><h1>{t.resultTitle}</h1><p className="muted">{a.test_title}</p></section>

    <section className="tx-result card" aria-label={t.resultTitle}>
      <div className="tx-score"><span>{t.score}</span><strong>{formatMarks(a.score_obtained)}<small> / {formatMarks(a.max_score)}</small></strong></div>
      <dl className="tx-stats">
        <div className="is-correct"><dt>{t.correctLabel}</dt><dd>{a.correct_answers}</dd></div>
        <div className="is-incorrect"><dt>{t.incorrectLabel}</dt><dd>{a.incorrect_answers}</dd></div>
        <div><dt>{t.unansweredLabel}</dt><dd>{a.unanswered_questions}</dd></div>
        <div><dt>{t.accuracy}</dt><dd>{Math.round(a.accuracy)}%</dd></div>
      </dl>
      <div className="tx-result-actions"><Link className="button button-secondary" to="/tests">{t.backToTests}</Link></div>
    </section>

    <section className="tx-review" aria-labelledby="review-heading">
      <h2 id="review-heading">{t.reviewTitle}</h2>
      <div className="tx-tabs" role="tablist" aria-label={t.reviewTitle}>
        {filters.map((entry) => <button key={entry.id} role="tab" aria-selected={filter === entry.id} className={filter === entry.id ? 'is-active' : ''} onClick={() => setFilter(entry.id)}>{entry.label} <small>{entry.count}</small></button>)}
      </div>
      {review.isPending ? <div className="planner-state card">{t.loadingResult}</div> : review.isError ? <div className="planner-state card" role="alert">{review.error.message}</div> : visible.length === 0 ? <p className="muted">{t.nothingToShow}</p> : <ol className="tx-review-list">
        {visible.map(({ item, number }) => <ReviewCard key={item.question.id} item={item} number={number + 1} language={language} t={t} />)}
      </ol>}
    </section>
  </AppShell>
}

function ReviewCard({ item, number, language, t }: { item: ReviewItem; number: number; language: string; t: Record<string, string> }) {
  const state = outcome(item)
  const explanation = pickText(language, item.explanation, item.explanation_hi)
  const options = [...item.question.options].sort((x, y) => x.key.localeCompare(y.key))
  return <li className={`tx-review-card card is-${state}`}>
    <header><b>{t.question} {number}</b><span className={`tx-pill is-${state}`}>{state === 'correct' ? t.correctLabel : state === 'incorrect' ? t.incorrectLabel : t.notAttempted}</span></header>
    <p className="tx-qtext">{pickText(language, item.question.text, item.question.text_hi)}</p>
    <ul className="tx-review-options">
      {options.map((option, position) => {
        const isCorrect = option.key === item.correct_option_key
        const isSelected = option.key === item.selected_option_key
        return <li key={option.id} className={`${isCorrect ? 'is-correct' : ''} ${isSelected && !isCorrect ? 'is-wrong' : ''}`}>
          <span className="tx-key" aria-hidden="true">{String.fromCharCode(65 + position)}</span>
          <span className="tx-option-text">{pickText(language, option.text, option.text_hi)}</span>
          {isCorrect && <span className="tx-tag"><Check size={13} />{t.correctAnswer}</span>}
          {isSelected && !isCorrect && <span className="tx-tag"><X size={13} />{t.yourAnswer}</span>}
          {isSelected && isCorrect && <span className="tx-tag">{t.yourAnswer}</span>}
        </li>
      })}
    </ul>
    {explanation && <p className="tx-explanation"><b>{t.explanationLabel}:</b> {explanation}</p>}
  </li>
}
