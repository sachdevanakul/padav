import { useEffect, useMemo, useState } from 'react'
import { ArrowLeft, ArrowRight, Check, Search } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { authStore } from '../store/auth'

export default function ExamSelectionPage() {
  const [category, setCategory] = useState('All')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<string[]>([])
  const token = authStore((state) => state.accessToken)
  const navigate = useNavigate()
  const examsQuery = useQuery({ queryKey: ['exams'], queryFn: api.exams })
  const savedQuery = useQuery({ queryKey: ['my-exams'], queryFn: api.myExams, enabled: Boolean(token) })
  const save = useMutation({ mutationFn: async () => {
    if (!token) throw new Error('Sign in to save your exam preferences.')
    const existing = await api.myExams()
    for (const item of existing) if (!selected.includes(item.exam_id)) await api.removeExam(item.exam_id)
    const currentIds = new Set(existing.map((item) => item.exam_id))
    for (const [index, id] of selected.entries()) if (!currentIds.has(id)) await api.addExam(id, index === 0)
    localStorage.removeItem('padav-selected-exams')
  }, onSuccess: () => navigate('/') })
  const exams = examsQuery.data || []
  const categories = useMemo(() => ['All', ...new Set(exams.map((exam) => exam.category).filter(Boolean))], [exams])
  useEffect(() => {
    if (token && savedQuery.data) setSelected(savedQuery.data.map((item) => item.exam_id))
  }, [token, savedQuery.data])
  const filtered = useMemo(() => exams.filter((exam) => (category === 'All' || exam.category.toLowerCase().includes(category.toLowerCase())) && `${exam.name} ${exam.category}`.toLowerCase().includes(search.toLowerCase())), [exams, category, search])
  function toggle(id: string) { setSelected((value) => value.includes(id) ? value.filter((item) => item !== id) : [...value, id]) }

  return <div className="selection-page"><header className="selection-header"><Link to="/" className="brand"><span className="brand-mark"><span>P</span></span><span>PADAV<small>YOUR AMBITION. YOUR ADVANTAGE.</small></span></Link><span className="step-note">PERSONALIZE YOUR PREPARATION <b>02 / 02</b></span></header><main className="selection-main"><Link to="/" className="back-link"><ArrowLeft size={16} /> Back to dashboard</Link><div className="selection-intro"><p className="eyebrow">YOUR GOALS, YOUR ROADMAP</p><h1>Which exams are<br /><span>you preparing for?</span></h1><p>Choose all that apply. We’ll shape your study space around your goals.</p></div>
    <label className="exam-search"><Search size={18} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search exams…" /></label>
    <div className="category-pills" role="tablist" aria-label="Filter exams">{categories.map((item) => <button key={item} type="button" role="tab" aria-selected={category === item} className={category === item ? 'selected' : ''} onClick={() => setCategory(item)}>{item}</button>)}</div>
    {examsQuery.isLoading ? <div className="exam-grid" aria-busy="true" aria-label="Loading exam options">{[0, 1, 2, 3].map((item) => <div key={item} className="phase6-skeleton" />)}</div>
      : examsQuery.error ? <div className="form-error" role="alert">Couldn’t load exams: {(examsQuery.error as Error).message}<button className="button button-secondary" onClick={() => void examsQuery.refetch()}>Try again</button></div>
      : exams.length === 0 ? <div className="empty-state card"><h2>No exams available</h2><p>There are no exam options to select right now.</p></div>
      : filtered.length === 0 ? <div className="empty-state card"><h2>No exams found</h2><p>Try a different search or category.</p></div>
      : <div className="exam-grid" aria-live="polite">{filtered.map((exam, index) => <button key={exam.id} type="button" onClick={() => toggle(exam.id)} className={`exam-card phase6-enter ${selected.includes(exam.id) ? 'chosen' : ''}`} style={{ animationDelay: `${index * 35}ms` }} aria-pressed={selected.includes(exam.id)} disabled={Boolean(token) && savedQuery.isLoading}><span className={`exam-badge category-${exam.category.toLowerCase()}`}>{exam.category.slice(0, 3).toUpperCase()}</span><span className="exam-card-copy"><b>{exam.name}</b><small>{exam.description || 'Build a focused preparation plan for this examination.'}</small></span><span className="exam-check">{selected.includes(exam.id) && <Check size={15} />}</span></button>)}</div>}
    {Boolean(token) && savedQuery.isError && <div className="form-error selection-error" role="alert">{(savedQuery.error as Error).message}<button className="button button-secondary" onClick={() => void savedQuery.refetch()}>Try again</button></div>}
    {save.error && <div className="form-error selection-error">{(save.error as Error).message}</div>}
    <footer className="selection-footer"><span>{selected.length} exam{selected.length === 1 ? '' : 's'} selected</span><button className="button button-primary" disabled={!selected.length || save.isPending || examsQuery.isLoading || examsQuery.isError || (Boolean(token) && (savedQuery.isLoading || savedQuery.isError))} onClick={() => save.mutate()}>{save.isPending ? 'Saving…' : 'Save my exams'}<ArrowRight size={17} /></button></footer>
  </main></div>
}
