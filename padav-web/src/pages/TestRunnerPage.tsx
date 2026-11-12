import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Navigate, useNavigate, useParams, Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, ArrowLeft, ArrowRight, Check, Clock3, Flag, Loader2, Send } from 'lucide-react'
import { QuestionPalette } from '../components/tests/QuestionPalette'
import { Modal } from '../components/ui/Modal'
import { useCountdown } from '../hooks/useCountdown'
import { formatClock } from '../lib/dates'
import { formatMarks, pickText } from '../lib/localize'
import { api, type AttemptDetail, type Question } from '../services/api'
import { translations } from '../locales/translations'
import { preferencesStore } from '../store/preferences'
import '../styles/tests.css'

type SaveState = 'idle' | 'saving' | 'saved' | 'error'
type Phase = 'running' | 'confirm' | 'timeup'

export default function TestRunnerPage() {
  const { attemptId = '' } = useParams()
  const language = preferencesStore((state) => state.language)
  const t = translations[language]
  // Fetched fresh on every mount so the server-side countdown is current; never refetched mid-test.
  const attempt = useQuery({ queryKey: ['attempt', attemptId], queryFn: () => api.attempt(attemptId), staleTime: Infinity, gcTime: 0, refetchOnMount: 'always', refetchOnReconnect: false })
  const open = attempt.data !== undefined && !attempt.data.is_submitted
  const questions = useQuery({ queryKey: ['attempt-questions', attemptId], queryFn: () => api.attemptQuestions(attemptId), enabled: open, staleTime: Infinity, gcTime: 0, refetchOnReconnect: false })

  if (attempt.data?.is_submitted) return <Navigate to={`/tests/attempts/${attemptId}/result`} replace />
  if (attempt.isError || questions.isError) return <div className="tx-fullpage"><div className="tx-state card" role="alert"><AlertTriangle size={22} /><p>{t.attemptLoadFailed}</p><Link className="button button-secondary" to="/tests">{t.backToTests}</Link></div></div>
  if (!attempt.data || !questions.data) return <div className="tx-fullpage"><div className="tx-state card"><Loader2 className="tx-spin" size={22} /><p>{t.loadingAttempt}</p></div></div>
  return <Runner attempt={attempt.data} questions={questions.data} />
}

function Runner({ attempt, questions }: { attempt: AttemptDetail; questions: Question[] }) {
  const { language, setLanguage } = preferencesStore()
  const t = translations[language]
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [index, setIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string | null>>(() => Object.fromEntries(attempt.answers.map((a) => [a.question_id, a.selected_option_key])))
  const [marked, setMarked] = useState<Set<string>>(new Set())
  const [phase, setPhase] = useState<Phase>('running')
  const [saveState, setSaveState] = useState<SaveState>('idle')
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [initialSeconds] = useState(attempt.seconds_remaining)

  const dirty = useRef(new Map<string, string | null>())
  const inFlight = useRef<Promise<boolean> | null>(null)
  const submittingRef = useRef(false)

  const question = questions[index]
  const options = useMemo(() => [...(question?.options ?? [])].sort((a, b) => a.key.localeCompare(b.key)), [question])
  const answeredCount = questions.filter((q) => answers[q.id]).length

  /** Sends every unsaved answer, oldest first. Later edits to the same question are never lost. */
  const flush = useCallback(async (): Promise<boolean> => {
    if (inFlight.current) await inFlight.current
    if (dirty.current.size === 0) return true
    const run = (async () => {
      setSaveState('saving')
      try {
        while (dirty.current.size > 0) {
          const [questionId, key] = dirty.current.entries().next().value as [string, string | null]
          await api.saveAnswer(attempt.id, questionId, key)
          if (dirty.current.get(questionId) === key) dirty.current.delete(questionId)
        }
        setSaveState('saved')
        return true
      } catch {
        setSaveState('error')
        return false
      } finally {
        inFlight.current = null
      }
    })()
    inFlight.current = run
    return run
  }, [attempt.id])

  const choose = useCallback((key: string | null) => {
    const current = questions[index]
    if (!current) return
    setAnswers((prev) => ({ ...prev, [current.id]: key }))
    dirty.current.set(current.id, key)
    void flush()
  }, [flush, index, questions])

  const submit = useCallback(async (automatic: boolean) => {
    if (submittingRef.current) return
    submittingRef.current = true
    setSubmitting(true)
    setSubmitError('')
    try {
      const saved = await flush()
      // A manual submit waits for every answer to be stored; on timeout we submit regardless.
      if (!saved && !automatic) throw new Error(t.saveFailed)
      await api.submitAttempt(attempt.id)
      await queryClient.invalidateQueries({ queryKey: ['attempts'] })
      navigate(`/tests/attempts/${attempt.id}/result`, { replace: true })
    } catch (cause) {
      submittingRef.current = false
      setSubmitting(false)
      setSubmitError(cause instanceof Error && cause.message === t.saveFailed ? t.saveFailed : t.submitFailed)
    }
  }, [attempt.id, flush, navigate, queryClient, t.saveFailed, t.submitFailed])

  const left = useCountdown(initialSeconds, () => { setPhase('timeup'); void submit(true) })

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault() }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [])

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (phase !== 'running' || event.metaKey || event.ctrlKey || event.altKey) return
      const target = event.target as HTMLElement | null
      if (target?.tagName === 'INPUT') return // radios handle their own arrow keys
      if (event.key === 'ArrowRight') setIndex((value) => Math.min(value + 1, questions.length - 1))
      else if (event.key === 'ArrowLeft') setIndex((value) => Math.max(value - 1, 0))
      else {
        const position = /^[1-5]$/.test(event.key) ? Number(event.key) - 1 : 'abcde'.indexOf(event.key.toLowerCase())
        const option = position >= 0 ? options[position] : undefined
        if (option && event.key.length === 1) choose(option.key)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [choose, options, phase, questions.length])

  if (!question) return null
  const selected = answers[question.id] ?? null
  const isMarked = marked.has(question.id)
  const low = left !== null && left <= 60

  function toggleMark() {
    setMarked((prev) => {
      const next = new Set(prev)
      if (next.has(question.id)) next.delete(question.id); else next.add(question.id)
      return next
    })
  }

  const notAnswered = questions.length - answeredCount
  return <div className="tx-fullpage tx-runner">
    <header className="tx-runner-head card">
      <div className="tx-runner-title"><p className="eyebrow">PADAV TEST</p><h1>{attempt.test_title}</h1></div>
      <div className={`tx-timer ${low ? 'is-low' : ''}`} role="timer" aria-label={t.timeLeft}><Clock3 size={16} /><span>{left === null ? '--:--' : formatClock(left)}</span></div>
      <div className="tx-runner-actions">
        <button className="icon-button lang-button" aria-label="Change language" onClick={() => setLanguage(language === 'en' ? 'hi' : 'en')}>{language === 'en' ? 'HI' : 'EN'}</button>
        <button className="button button-primary" onClick={() => { setSubmitError(''); setPhase('confirm') }}><Send size={15} />{t.submitTest}</button>
      </div>
    </header>

    <div className="tx-runner-body">
      <section key={question.id} className="tx-question card" aria-labelledby="tx-qtext">
        <header className="tx-question-meta">
          <strong>{t.question} {index + 1} {t.of} {questions.length}</strong>
          <span>+{formatMarks(question.marks)}{question.negative_marks > 0 ? ` / −${formatMarks(question.negative_marks)}` : ''}</span>
        </header>
        <h2 id="tx-qtext" className="tx-qtext">{pickText(language, question.text, question.text_hi)}</h2>
        <fieldset className="tx-options">
          <legend className="tx-sr">{t.question} {index + 1}</legend>
          {options.map((option, position) => <label key={option.id} className={`tx-option ${selected === option.key ? 'is-selected' : ''}`}>
            <input type="radio" name={`q-${question.id}`} value={option.key} checked={selected === option.key} onChange={() => choose(option.key)} />
            <span className="tx-key" aria-hidden="true">{String.fromCharCode(65 + position)}</span>
            <span className="tx-option-text">{pickText(language, option.text, option.text_hi)}</span>
            {selected === option.key && <Check size={16} aria-hidden="true" />}
          </label>)}
        </fieldset>
        <footer className="tx-question-actions">
          <button className="button button-ghost" onClick={() => choose(null)} disabled={selected === null}>{t.clearResponse}</button>
          <button className={`button button-secondary ${isMarked ? 'is-active' : ''}`} onClick={toggleMark} aria-pressed={isMarked}><Flag size={15} />{isMarked ? t.unmarkReview : t.markReview}</button>
          <span className="tx-spacer" />
          <button className="button button-secondary" onClick={() => setIndex(index - 1)} disabled={index === 0}><ArrowLeft size={15} />{t.previous}</button>
          <button className="button button-primary" onClick={() => setIndex(index + 1)} disabled={index === questions.length - 1}>{t.next}<ArrowRight size={15} /></button>
        </footer>
      </section>

      <aside className="tx-palette card" aria-label={t.palette}>
        <h2>{t.palette}</h2>
        <QuestionPalette
          total={questions.length}
          current={index}
          isAnswered={(i) => Boolean(answers[questions[i]!.id])}
          isMarked={(i) => marked.has(questions[i]!.id)}
          onSelect={setIndex}
          labels={{ answered: t.answered, notAnswered: t.notAnswered, marked: t.markedLabel, question: t.question, palette: t.palette }}
        />
        <ul className="tx-legend">
          <li><i className="tx-dot is-answered" />{t.answered} · {answeredCount}</li>
          <li><i className="tx-dot" />{t.notAnswered} · {notAnswered}</li>
          <li><i className="tx-dot is-marked" />{t.markedLabel} · {marked.size}</li>
        </ul>
        <p className={`tx-save is-${saveState}`} role="status">
          {saveState === 'saving' && t.saving}
          {saveState === 'saved' && t.saved}
          {saveState === 'error' && <button className="tx-link" onClick={() => void flush()}>{t.saveFailed}</button>}
        </p>
      </aside>
    </div>

    <Modal isOpen={phase !== 'running'} onClose={() => setPhase('running')} title={phase === 'timeup' ? t.timeUp : t.confirmSubmitTitle} ariaLabelledBy="tx-modal-title" role="alertdialog" dismissible={phase === 'confirm' && !submitting} showCloseButton={false} className="tx-modal card">
        <h2 id="tx-modal-title">{phase === 'timeup' ? t.timeUp : t.confirmSubmitTitle}</h2>
        {phase === 'confirm' && <>
          <ul className="tx-summary">
            <li><b>{answeredCount}</b>{t.answered}</li>
            <li><b>{notAnswered}</b>{t.notAnswered}</li>
            <li><b>{marked.size}</b>{t.markedLabel}</li>
          </ul>
          <p className="muted">{t.confirmSubmitBody}</p>
        </>}
        {submitError && <p className="tx-error" role="alert">{submitError}</p>}
        <footer>
          {phase === 'confirm' && <button className="button button-ghost" onClick={() => setPhase('running')} disabled={submitting}>{t.keepWorking}</button>}
          <button className="button button-primary" onClick={() => void submit(phase === 'timeup')} disabled={submitting}>{submitting ? t.submitting : t.submitTest}</button>
        </footer>
    </Modal>
  </div>
}
