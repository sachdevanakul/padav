import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { ArrowRight, ArrowUpRight, BookOpen, Check, Clock3, Flame, Sparkles, Target, Trophy, Zap } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import AppShell from '../layouts/AppShell'
import { api, type Course } from '../services/api'
import { authStore } from '../store/auth'
import { preferencesStore } from '../store/preferences'
import { translations } from '../locales/translations'

const demoCourses: Course[] = [
  { id: 'demo-quant', subject_id: '', title: 'Quantitative Aptitude: Core Concepts', title_hi: 'मात्रात्मक योग्यता', description: 'Build speed and accuracy from the ground up.', instructor: 'Aarav Mehta', level: 'beginner', total_lessons: 24, estimated_hours: 8, thumbnail_url: null, is_free: true, is_active: true, created_at: '' },
  { id: 'demo-reason', subject_id: '', title: 'Reasoning: Patterns & Logic', title_hi: 'रीज़निंग', description: 'Sharpen your approach to high-frequency question types.', instructor: 'Isha Verma', level: 'intermediate', total_lessons: 18, estimated_hours: 6, thumbnail_url: null, is_free: true, is_active: true, created_at: '' },
  { id: 'demo-english', subject_id: '', title: 'English: Grammar in Context', title_hi: 'अंग्रेज़ी', description: 'Make grammar rules stick through practical examples.', instructor: 'Maya Kapoor', level: 'beginner', total_lessons: 16, estimated_hours: 5, thumbnail_url: null, is_free: true, is_active: true, created_at: '' },
]
const week = [{ day: 'Mon', score: 45 }, { day: 'Tue', score: 62 }, { day: 'Wed', score: 54 }, { day: 'Thu', score: 77 }, { day: 'Fri', score: 68 }, { day: 'Sat', score: 91 }, { day: 'Sun', score: 82 }]

function getDailyMission(): boolean {
  return localStorage.getItem(`padav-mission-${new Date().toDateString()}`) === 'done'
}

export default function DashboardPage() {
  const user = authStore((state) => state.user)
  const language = preferencesStore((state) => state.language)
  const t = translations[language]
  const [missionDone, setMissionDone] = useState(getDailyMission)
  const courseQuery = useQuery({ queryKey: ['courses'], queryFn: api.courses })
  const overviewQuery = useQuery({ queryKey: ['overview'], queryFn: api.overview, enabled: Boolean(user) })
  const courses = courseQuery.data?.length ? courseQuery.data : demoCourses
  const displayName = user?.full_name?.split(' ')[0] || (language === 'hi' ? 'विद्यार्थी' : 'there')
  const hour = new Date().getHours()
  const greeting = hour < 12 ? t.greeting : hour < 17 ? (language === 'hi' ? 'नमस्कार' : 'Good afternoon') : (language === 'hi' ? 'शुभ संध्या' : 'Good evening')
  const overview = overviewQuery.data
  const today = useMemo(() => new Intl.DateTimeFormat(language === 'hi' ? 'hi-IN' : 'en-IN', { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date()), [language])

  function completeMission() {
    const next = !missionDone
    setMissionDone(next)
    const key = `padav-mission-${new Date().toDateString()}`
    if (next) localStorage.setItem(key, 'done')
    else localStorage.removeItem(key)
  }

  return <AppShell>
    <section className="dashboard-heading"><div><p className="eyebrow">{today.toUpperCase()} <span className="eyebrow-spark">✦</span></p><h1>{greeting}, <span>{displayName}</span></h1><p className="muted">{t.welcome}</p></div><Link to="/exams" className="exam-switcher"><span className="exam-switch-icon"><Target size={16} /></span><span>My exams<small>Personalize your plan</small></span><ArrowRight size={15} /></Link></section>
    {!user && <div className="preview-banner"><Sparkles size={16} /><span><b>Preview mode</b> — create an account to save exam preferences and sync your learning.</span><Link to="/auth/register">Create account <ArrowRight size={14} /></Link></div>}

    <div className="dashboard-grid">
      <article className="mission-card card"><div className="mission-copy"><div className="card-kicker"><span className="kicker-icon purple"><Target size={15} /></span>{t.mission}<span className="today-pill">TODAY</span></div><h2>Build your rhythm,<br /><span>one session at a time.</span></h2><p>30 minutes of focused practice is a strong start.</p><button className={`mission-action ${missionDone ? 'done' : ''}`} onClick={completeMission}>{missionDone ? <><Check size={16} /> Mission complete</> : <>Mark today’s session <ArrowRight size={16} /></>}</button></div><div className="mission-ring-wrap"><div className="mission-ring"><svg viewBox="0 0 120 120" aria-hidden="true"><circle className="ring-track" cx="60" cy="60" r="49" /><circle className="ring-value" cx="60" cy="60" r="49" style={{ strokeDasharray: '308', strokeDashoffset: missionDone ? '0' : '220' }} /></svg><span><b>{missionDone ? '30' : '0'}<small>/30m</small></b><small>STUDY GOAL</small></span></div><div className="ring-glow" /></div></article>
      <article className="streak-card card"><div className="card-kicker"><span className="kicker-icon orange"><Flame size={15} /></span>{t.streak}</div><div className="streak-number">{overview?.current_streak ?? 0}<span> days</span></div><p className="muted">Consistency is your superpower.</p><div className="streak-week">{['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, index) => <span key={index} className={index < (overview?.current_streak ? Math.min(overview.current_streak, 5) : 0) ? 'checked' : ''}><small>{day}</small>{index < (overview?.current_streak ? Math.min(overview.current_streak, 5) : 0) ? <Check size={12} /> : <i />}</span>)}</div><span className="streak-flame"><Flame size={72} /></span></article>
      <article className="performance-card card"><div className="card-title-row"><div><div className="card-kicker"><span className="kicker-icon blue"><Zap size={15} /></span>Performance snapshot</div><p className="muted">Sample weekly trend</p></div><button className="period-select">This week <span aria-hidden="true">⌄</span></button></div><div className="performance-metrics"><Metric icon={<Target size={15} />} label={t.accuracy} value={`${overview?.overall_accuracy ?? 0}%`} delta={overview ? 'ACCOUNT' : 'SAMPLE'} /><Metric icon={<BookOpen size={15} />} label={t.questions} value={overview?.total_questions_attempted ?? 0} delta={overview ? 'ACCOUNT' : 'SAMPLE'} /><Metric icon={<Clock3 size={15} />} label={t.hours} value={`${overview?.total_study_hours ?? 0}h`} delta={overview ? 'ACCOUNT' : 'SAMPLE'} /></div><div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={week} margin={{ top: 10, right: 8, left: -24, bottom: 0 }}><defs><linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="var(--color-primary)" stopOpacity={.28} /><stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0} /></linearGradient></defs><CartesianGrid vertical={false} stroke="var(--color-grid)" strokeDasharray="4 5" /><XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: 'var(--color-muted)', fontSize: 11 }} dy={9} /><YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--color-muted)', fontSize: 10 }} ticks={[0, 25, 50, 75, 100]} /><Tooltip contentStyle={{ background: 'var(--color-elevated)', border: '1px solid var(--color-border)', borderRadius: 12, color: 'var(--color-text)' }} /><Area type="monotone" dataKey="score" stroke="var(--color-primary)" strokeWidth={2.5} fill="url(#scoreFill)" activeDot={{ r: 4, fill: 'var(--color-primary)' }} /></AreaChart></ResponsiveContainer></div></article>
      <article className="challenge-card card"><div className="challenge-decoration"><div className="challenge-orbit orbit-a" /><div className="challenge-orbit orbit-b" /><span><Zap size={24} fill="currentColor" /></span></div><div className="challenge-content"><div className="card-kicker">DAILY CHALLENGE <span className="new-pill">5 MIN</span></div><h3>Sharpen your<br />reasoning edge.</h3><p>5 questions · Mixed difficulty</p><Link className="challenge-link" to="/tests">Explore practice <ArrowRight size={16} /></Link></div></article>
      <section className="courses-section"><div className="section-heading"><div><p className="eyebrow">CURATED FOR YOUR GOALS</p><h2>{t.courses}</h2></div><Link to="/learn" className="text-link">Explore library <ArrowRight size={15} /></Link></div>{(!courseQuery.data?.length || courseQuery.isError) && <p className="inline-notice">Sample courses shown while no course catalog is available.</p>}<div className="course-row">{courses.slice(0, 3).map((course, index) => <CourseCard key={course.id} course={course} index={index} />)}</div></section>
      <article className="upcoming-card card"><div className="section-heading compact"><div><p className="eyebrow">STAY AHEAD</p><h2>{t.upcoming}</h2></div><span className="calendar-badge">2026</span></div><div className="upcoming-empty"><span className="calendar-icon"><Trophy size={20} /></span><div><b>Your next mock test</b><p>Practice tests will appear here as they’re published.</p></div><ArrowRight size={16} /></div></article>
    </div>
  </AppShell>
}

function Metric({ icon, label, value, delta }: { icon: ReactNode; label: string; value: string | number; delta: string }) {
  return <div className="performance-metric"><span className="metric-label">{icon}{label}</span><strong>{value}</strong><small className="delta-up"><ArrowUpRight size={12} />{delta}</small></div>
}

function CourseCard({ course, index }: { course: Course; index: number }) {
  const themes = ['course-art-lilac', 'course-art-blue', 'course-art-mint']
  return <article className="course-card card"><div className={`course-art ${themes[index % themes.length]}`}><span className="course-art-mark">{['01', '02', '03'][index]}</span><span className="course-art-orbit" /><span className="course-art-name">{course.title.split(':')[0]}</span><span className="course-subject">{course.level}</span></div><div className="course-card-body"><div className="course-meta"><span>{course.total_lessons} LESSONS</span><span><Clock3 size={12} /> {course.estimated_hours}H</span></div><h3>{course.title}</h3><p>{course.description || 'A structured learning path to help you make steady progress.'}</p><div className="course-progress"><span><i style={{ width: '0%' }} /></span><small>Not started</small></div><Link to="/learn" className="course-continue">Browse course <ArrowRight size={14} /></Link></div></article>
}
