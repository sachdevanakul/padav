import { useCallback, useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, ArrowLeft, ArrowRight, Check, Clock3, Loader2, Send } from 'lucide-react'
import { Modal } from '../ui/Modal'
import { useCountdown } from '../../hooks/useCountdown'
import { formatClock } from '../../lib/dates'
import { ApiError, api, type PiaRun } from '../../services/api'
import { translations } from '../../locales/translations'
import { preferencesStore } from '../../store/preferences'
import '../../styles/tests.css'
import '../../styles/pia.css'

type Save = 'idle' | 'saving' | 'saved' | 'error'

/** One timed subtest. The server owns the clock; this countdown only mirrors it and asks the server what happened. */
export function PiaRunner({ sessionId, run, onDone }: { sessionId: string; run: PiaRun; onDone: () => void }) {
  const t = translations[preferencesStore((state) => state.language)]
  const items = useQuery({ queryKey: ['pia-items', sessionId, run.domain], queryFn: () => api.piaItems(sessionId, run.domain), staleTime: Infinity, gcTime: 0, refetchOnReconnect: false })
  const queryClient = useQueryClient()
  const [index, setIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string | null>>({})
  const [seeded, setSeeded] = useState(false)
  const [save, setSave] = useState<Save>('idle')
  const [confirm, setConfirm] = useState(false)
  const [timeUp, setTimeUp] = useState(false)
  const [offline, setOffline] = useState(false)
  const [initialSeconds] = useState(run.seconds_remaining)
  const shownAt = useRef(performance.now())
  const queue = useRef(Promise.resolve())
  const ended = useRef(false)

  useEffect(() => {
    if (items.data && !seeded) { setAnswers(Object.fromEntries(items.data.map((i) => [i.item_code, i.selected_key]))); setSeeded(true) }
  }, [items.data, seeded])
  useEffect(() => { shownAt.current = performance.now() }, [index])

  const finish = useCallback(async () => {
    if (ended.current) return
    ended.current = true
    await queue.current.catch(() => undefined) // let in-flight answers land first
    await queryClient.invalidateQueries({ queryKey: ['pia-session', sessionId] })
    onDone()
  }, [onDone, queryClient, sessionId])

  const left = useCountdown(initialSeconds, () => { setTimeUp(true); window.setTimeout(() => void finish(), 1500) })

  const complete = useMutation({ mutationFn: () => api.piaComplete(sessionId, run.domain), onSuccess: () => void finish() })

  // Answers are sent one at a time in order, so the server log reflects exactly what the learner did.
  const choose = useCallback((key: string | null) => {
    const item = items.data?.[index]
    if (!item || ended.current) return
    const elapsed = Math.round(performance.now() - shownAt.current)
    setAnswers((prev) => ({ ...prev, [item.item_code]: key }))
    setSave('saving')
    queue.current = queue.current.then(async () => {
      try {
        await api.piaAnswer(sessionId, run.domain, item.item_code, key, elapsed)
        setSave('saved')
      } catch (error) {
        if (error instanceof ApiError && error.status === 409) { setTimeUp(true); void finish() } // server says time is up
        else setSave('error')
      }
    })
  }, [finish, index, items.data, run.domain, sessionId])

  // Connection loss is recorded as an interruption (the timer is not paused; analysts apply the exclusion policy).
  useEffect(() => {
    const send = (type: 'interruption' | 'resume', reason: string) => void api.piaEvent(sessionId, run.domain, type, { reason }).catch(() => undefined)
    const down = () => { setOffline(true); send('interruption', 'offline') }
    const up = () => { setOffline(false); send('resume', 'online') }
    const visibility = () => send(document.hidden ? 'interruption' : 'resume', 'tab-hidden')
    window.addEventListener('offline', down); window.addEventListener('online', up); document.addEventListener('visibilitychange', visibility)
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault() }
    window.addEventListener('beforeunload', warn)
    return () => {
      window.removeEventListener('offline', down); window.removeEventListener('online', up)
      document.removeEventListener('visibilitychange', visibility); window.removeEventListener('beforeunload', warn)
    }
  }, [run.domain, sessionId])

  if (items.isError) return <div className="tx-fullpage"><div className="tx-state card" role="alert"><AlertTriangle size={22} /><p>{t.piaLoadFailed}</p><button className="button button-secondary" onClick={onDone}>{t.piaBackToAssessment}</button></div></div>
  if (!items.data || !seeded) return <div className="tx-fullpage"><div className="tx-state card"><Loader2 className="tx-spin" size={22} /></div></div>
  const item = items.data[index]
  if (!item) return null
  const selected = answers[item.item_code] ?? null
  const unanswered = items.data.filter((i) => !answers[i.item_code]).length
  const low = left !== null && left <= 60
  const title = t[`piaDomain_${run.domain}`] ?? run.label

  return <div className="tx-fullpage tx-runner">
    <header className="tx-runner-head card">
      <div className="tx-runner-title"><p className="eyebrow">PIA · {run.sequence}/7</p><h1>{title}</h1></div>
      <div className={`tx-timer ${low ? 'is-low' : ''}`} role="timer" aria-label={t.timeLeft}><Clock3 size={16} /><span>{left === null ? '--:--' : formatClock(left)}</span></div>
      <div className="tx-runner-actions"><button className="button button-primary" onClick={() => setConfirm(true)}><Send size={15} />{t.piaFinishSection}</button></div>
    </header>
    {offline && <p className="pia-banner" role="alert"><AlertTriangle size={16} />{t.piaOffline}</p>}
    {timeUp && <p className="pia-banner" role="alert"><Clock3 size={16} />{t.piaTimeUp}</p>}

    <div className="pia-runner-body">
      <section key={item.item_code} className="tx-question card" aria-labelledby="pia-stem">
        <header className="tx-question-meta"><strong>{t.question} {index + 1} {t.of} {items.data.length}</strong></header>
        <h2 id="pia-stem" className="tx-qtext">{item.stem}</h2>
        <fieldset className="tx-options" disabled={timeUp}>
          <legend className="tx-sr">{t.question} {index + 1}</legend>
          {item.options.map((option, position) => <label key={option.key} className={`tx-option ${selected === option.key ? 'is-selected' : ''}`}>
            <input type="radio" name={`pia-${item.item_code}`} value={option.key} checked={selected === option.key} onChange={() => choose(option.key)} />
            <span className="tx-key" aria-hidden="true">{String.fromCharCode(65 + position)}</span>
            <span className="tx-option-text">{option.text}</span>
            {selected === option.key && <Check size={16} aria-hidden="true" />}
          </label>)}
        </fieldset>
        <footer className="tx-question-actions">
          <button className="button button-ghost" onClick={() => choose(null)} disabled={selected === null || timeUp}>{t.clearResponse}</button>
          <span className="tx-spacer" />
          <button className="button button-secondary" onClick={() => setIndex(index - 1)} disabled={index === 0}><ArrowLeft size={15} />{t.previous}</button>
          <button className="button button-primary" onClick={() => setIndex(index + 1)} disabled={index === items.data.length - 1}>{t.next}<ArrowRight size={15} /></button>
        </footer>
        <p className={`tx-save is-${save}`} role="status">{save === 'saving' && t.saving}{save === 'saved' && t.saved}{save === 'error' && t.saveFailed}</p>
      </section>

      <nav className="card pia-dots" aria-label={t.palette}>
        {items.data.map((entry, i) => <button key={entry.item_code} className={`pia-dot ${i === index ? 'is-current' : ''} ${answers[entry.item_code] ? 'is-answered' : ''}`} onClick={() => setIndex(i)} aria-label={`${t.question} ${i + 1}: ${answers[entry.item_code] ? t.answered : t.notAnswered}`} aria-current={i === index}>{i + 1}</button>)}
      </nav>
    </div>

    <Modal isOpen={confirm} onClose={() => setConfirm(false)} ariaLabelledBy="pia-confirm-title" role="alertdialog" showCloseButton={false}>
      <h2 id="pia-confirm-title">{t.piaFinishConfirmTitle}</h2>
      <p>{unanswered} {t.piaUnanswered}. {t.piaFinishConfirmBody}</p>
      <div className="pia-modal-actions">
        <button className="button button-secondary" onClick={() => setConfirm(false)}>{t.piaKeepWorking}</button>
        <button className="button button-primary" onClick={() => complete.mutate()} disabled={complete.isPending}>{t.piaFinishSection}</button>
      </div>
    </Modal>
  </div>
}
