import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import {
  ArrowRight,
  BookOpen,
  Check,
  Clock3,
  Flame,
  Sparkles,
  Target,
  Trophy,
  Zap,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import AppShell from '../layouts/AppShell'
import { currentWeekKeys, parseServerDate } from '../lib/dates'
import { pickText } from '../lib/localize'
import { useReducedMotion } from '../hooks/useReducedMotion'
import { api, type Course } from '../services/api'
import { authStore } from '../store/auth'
import { preferencesStore } from '../store/preferences'
import { translations } from '../locales/translations'
import '../styles/account.css'

function getDailyMission(): boolean {
  return localStorage.getItem(`padav-mission-${new Date().toDateString()}`) === 'done'
}

/* ---- Count-up animation hook ---- */
function useCountUp(target: number, duration = 1200, enabled = true, reducedMotion = false): number {
  const [value, setValue] = useState(0)
  useEffect(() => {
    if (!enabled || target === 0 || reducedMotion || typeof requestAnimationFrame !== 'function') {
      setValue(target)
      return
    }
    const start = performance.now()
    let rafId: number
    function step(now: number) {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      const ease = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(target * ease))
      if (progress < 1) rafId = requestAnimationFrame(step)
    }
    rafId = requestAnimationFrame(step)
    return () => cancelAnimationFrame(rafId)
  }, [target, duration, enabled, reducedMotion])
  return value
}

export default function DashboardPage() {
  const user = authStore((state) => state.user)
  const language = preferencesStore((state) => state.language)
  const t = translations[language]
  const [missionDone, setMissionDone] = useState(getDailyMission)
  const courseQuery = useQuery({ queryKey: ['courses'], queryFn: api.courses })
  const overviewQuery = useQuery({ queryKey: ['overview'], queryFn: api.overview, enabled: Boolean(user) })
  const trendsQuery = useQuery({ queryKey: ['trends'], queryFn: api.trends, enabled: Boolean(user) })
  const testsQuery = useQuery({ queryKey: ['tests'], queryFn: api.tests, enabled: Boolean(user) })
  const courses = courseQuery.data ?? []
  const nextTest = testsQuery.data?.[0]
  const trendPoints = (trendsQuery.data ?? []).slice(-7)
  const chartData = trendPoints.map((point) => ({ day: point.date ? new Intl.DateTimeFormat(language === 'hi' ? 'hi-IN' : 'en-IN', { day: 'numeric', month: 'short' }).format(parseServerDate(point.date)) : '', score: Math.round(point.accuracy) }))
  const weekKeys = useMemo(() => currentWeekKeys(), [])
  const activeDates = new Set(overviewQuery.data?.active_dates ?? [])
  const isActive = (index: number) => activeDates.has(weekKeys[index] ?? '')
  const displayName = user?.full_name?.split(' ')[0] || (language === 'hi' ? 'विद्यार्थी' : 'there')
  const hour = new Date().getHours()
  const greeting = hour < 12 ? t.greeting : hour < 17 ? (language === 'hi' ? 'नमस्कार' : 'Good afternoon') : (language === 'hi' ? 'शुभ संध्या' : 'Good evening')
  const overview = overviewQuery.data
  const today = useMemo(() => new Intl.DateTimeFormat(language === 'hi' ? 'hi-IN' : 'en-IN', { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date()), [language])
  const prefersReduced = useReducedMotion()

  const accuracyAnim = useCountUp(Math.round(overview?.overall_accuracy ?? 0), 1200, Boolean(overview), prefersReduced)
  const questionsAnim = useCountUp(overview?.total_questions_attempted ?? 0, 1200, Boolean(overview), prefersReduced)
  const hoursAnim = useCountUp(Math.round(overview?.total_study_hours ?? 0), 1200, Boolean(overview), prefersReduced)
  const streakAnim = useCountUp(overview?.current_streak ?? 0, 1200, Boolean(overview), prefersReduced)

  function completeMission() {
    const next = !missionDone
    setMissionDone(next)
    const key = `padav-mission-${new Date().toDateString()}`
    if (next) {
      localStorage.setItem(key, 'done')
    } else {
      localStorage.removeItem(key)
    }
  }

  return <AppShell>
    {/* Welcome header */}
    <section className="dashboard-heading pdv-animate-slide-in-up"><div><p className="eyebrow">{today.toUpperCase()} <span className="eyebrow-spark">✦</span></p><h1 className="pdv-text-2xl pdv-font-bold pdv-mt-2">{greeting}, <span className="pdv-text-primary">{displayName}</span></h1><p className="muted">{t.welcome}</p></div><Link to="/exams" className="exam-switcher pdv-hover-lift pdv-transition-colors"><span className="exam-switch-icon"><Target size={16} /></span><span>My exams<small>Personalize your plan</small></span><ArrowRight size={15} /></Link></section>
    {!user && <div className="preview-banner pdv-bg-raised pdv-border pdv-rounded pdv-p-4 pdv-mb-6 pdv-animate-fade-in"><Sparkles size={16} /><span><b>Preview mode</b> — create an account to save exam preferences and sync your learning.</span><Link to="/auth/register" className="pdv-btn-primary pdv-mt-3">Create account <ArrowRight size={14} /></Link></div>}
    {overviewQuery.isError && <p className="inline-notice" role="alert">{overviewQuery.error.message} <button className="button button-ghost" onClick={() => void overviewQuery.refetch()}>Try again</button></p>}
    {testsQuery.isError && <p className="inline-notice" role="alert">{testsQuery.error.message} <button className="button button-ghost" onClick={() => void testsQuery.refetch()}>Try again</button></p>}

    <div className="dashboard-grid">
      {/* Stat cards row */}
      <div className="stat-cards-row pdv-grid pdv-gap-4 pdv-mb-6">
        <article className="stat-card pdv-card pdv-shadow-sm pdv-hover-lift pdv-transition pdv-animate-scale-in" style={{ animationDelay: '100ms' }}>
          <div className="stat-header pdv-flex pdv-justify-between pdv-items-start">
            <div>
              <span className="stat-kicker pdv-text-xs pdv-font-semibold pdv-text-muted pdv-uppercase">{t.accuracy}</span>
            </div>
            <div className="stat-icon pdv-bg-mint-soft pdv-text-mint pdv-rounded-lg pdv-p-3"><Flame size={18} /></div>
          </div>
          <div className="stat-value pdv-text-3xl pdv-font-bold pdv-mt-2">{overview ? `${accuracyAnim}%` : '—'}</div>
          <p className="stat-label pdv-text-sm pdv-text-muted">Across all attempts</p>
        </article>
        <article className="stat-card pdv-card pdv-shadow-sm pdv-hover-lift pdv-transition pdv-animate-scale-in" style={{ animationDelay: '200ms' }}>
          <div className="stat-header pdv-flex pdv-justify-between pdv-items-start">
            <div>
              <span className="stat-kicker pdv-text-xs pdv-font-semibold pdv-text-muted pdv-uppercase">{t.questions}</span>
            </div>
            <div className="stat-icon pdv-bg-blue-soft pdv-text-blue pdv-rounded-lg pdv-p-3"><BookOpen size={18} /></div>
          </div>
          <div className="stat-value pdv-text-3xl pdv-font-bold pdv-mt-2">{overview ? questionsAnim : '—'}</div>
          <p className="stat-label pdv-text-sm pdv-text-muted">Questions attempted</p>
        </article>
        <article className="stat-card pdv-card pdv-shadow-sm pdv-hover-lift pdv-transition pdv-animate-scale-in" style={{ animationDelay: '300ms' }}>
          <div className="stat-header pdv-flex pdv-justify-between pdv-items-start">
            <div>
              <span className="stat-kicker pdv-text-xs pdv-font-semibold pdv-text-muted pdv-uppercase">{t.hours}</span>
            </div>
            <div className="stat-icon pdv-bg-purple-soft pdv-text-purple pdv-rounded-lg pdv-p-3"><Clock3 size={18} /></div>
          </div>
          <div className="stat-value pdv-text-3xl pdv-font-bold pdv-mt-2">{overview ? `${hoursAnim}h` : '—'}</div>
          <p className="stat-label pdv-text-sm pdv-text-muted">Total study time</p>
        </article>
        <article className="stat-card pdv-card pdv-shadow-sm pdv-hover-lift pdv-transition pdv-animate-scale-in" style={{ animationDelay: '400ms' }}>
          <div className="stat-header pdv-flex pdv-justify-between pdv-items-start">
            <div>
              <span className="stat-kicker pdv-text-xs pdv-font-semibold pdv-text-muted pdv-uppercase">{t.streak}</span>
            </div>
            <div className="stat-icon pdv-bg-orange-soft pdv-text-orange pdv-rounded-lg pdv-p-3"><Target size={18} /></div>
          </div>
          <div className="stat-value pdv-text-3xl pdv-font-bold pdv-mt-2">{overview ? streakAnim : '—'}</div>
          <p className="stat-label pdv-text-sm pdv-text-muted">Current learning streak</p>
        </article>
      </div>

      {/* Mission card */}
      <article className="mission-card card pdv-shadow-sm pdv-hover-lift pdv-transition pdv-animate-slide-in-up" style={{ animationDelay: '100ms' }}>
      <div className="mission-copy"><div className="card-kicker"><span className="kicker-icon purple"><Target size={15} /></span>{t.mission}<span className="today-pill">TODAY</span></div><h2>Build your rhythm,<br /><span>one session at a time.</span></h2><p>30 minutes of focused practice is a strong start.</p><button className={`mission-action pdv-btn-primary ${missionDone ? 'done' : ''}`} onClick={completeMission} aria-pressed={missionDone}>{missionDone ? <><Check size={16} /> Mission complete</> : <>Mark today’s session <ArrowRight size={16} /></>}</button></div><div className="mission-ring-wrap"><div className="mission-ring" aria-label={missionDone ? 'Daily mission complete' : 'Daily mission not complete'}><svg viewBox="0 0 120 120" aria-hidden="true"><circle className="ring-track" cx="60" cy="60" r="49" /><circle className="ring-value" cx="60" cy="60" r="49" style={{ strokeDasharray: '308', strokeDashoffset: missionDone ? '0' : '308', transition: prefersReduced ? 'none' : 'stroke-dashoffset 0.8s ease-out' }} /></svg><span aria-hidden="true"><b>{missionDone ? <Check size={24} /> : '0%'}</b><small>DAILY MISSION</small></span></div><div className={`ring-glow ${missionDone ? 'done' : ''}`} /></div></article>
      {/* Streak card */}
      <article className="streak-card card pdv-shadow-sm pdv-hover-lift pdv-transition pdv-animate-slide-in-up" style={{ animationDelay: '200ms' }}>
        <div className="card-kicker"><span className="kicker-icon orange"><Flame size={15} /></span>{t.streak}</div>
        <div className="streak-number">{overview ? streakAnim : '—'}<span> {language === 'hi' ? 'दिन' : 'days'}</span></div>
        <p className="muted">Consistency is your superpower.</p>
        <div className="streak-week">{['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, index) => <span key={index} className={isActive(index) ? 'checked' : ''}><small>{day}</small>{isActive(index) ? <Check size={12} /> : <i />}</span>)}</div>
        <span className="streak-flame"><Flame size={72} /></span>
      </article>
      {/* Performance snapshot + chart */}
      <article className="performance-card card pdv-shadow-sm pdv-hover-lift pdv-transition pdv-animate-slide-in-up" style={{ animationDelay: '300ms' }}>
        <div className="card-title-row"><div><div className="card-kicker"><span className="kicker-icon blue"><Zap size={15} /></span>Performance snapshot</div><p className="muted">{trendsQuery.isError ? trendsQuery.error.message : trendPoints.length ? t.trendTitle : t.trendEmpty}</p></div></div>
        <div className="performance-metrics pdv-grid pdv-gap-3 pdv-mb-6">
          <Metric icon={<Target size={15} />} label={t.accuracy} value={overview ? `${accuracyAnim}%` : '—'} />
          <Metric icon={<BookOpen size={15} />} label={t.questions} value={overview ? questionsAnim : '—'} />
          <Metric icon={<Clock3 size={15} />} label={t.hours} value={overview ? `${hoursAnim}h` : '—'} />
        </div>
        <div className="chart-wrap pdv-rounded-lg pdv-border pdv-p-4">{trendsQuery.isPending
          ? <div className="phase6-skeleton chart-loading" aria-label={t.loadingResult} />
          : trendPoints.length === 0 ? <p className="chart-empty">{trendsQuery.isError ? trendsQuery.error.message : t.trendEmpty}</p>
          : <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={chartData} margin={{ top: 10, right: 8, left: -24, bottom: 0 }}>
              <defs>
                <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.28} />
                  <stop offset="100%" stopColor="var(--primary)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} stroke="var(--grid)" strokeDasharray="4 5" />
              <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: 'var(--muted)', fontSize: 11 }} dy={9} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--muted)', fontSize: 10 }} ticks={[0, 25, 50, 75, 100]} />
              <Tooltip
                formatter={(value) => [`${value}%`, 'Accuracy']}
                contentStyle={{ background: 'var(--raised)', border: '1px solid var(--border)', borderRadius: 12, color: 'var(--text)' }}
                cursor={{ fill: 'var(--primary)' }}
              />
              <Area type="monotone" dataKey="score" stroke="var(--primary)" strokeWidth={2.5} fill="url(#scoreFill)" activeDot={{ r: 4, fill: 'var(--primary)' }} isAnimationActive={!prefersReduced} animationDuration={prefersReduced ? 0 : 1500} animationEasing="ease-out" />
            </AreaChart>
          </ResponsiveContainer>}
        </div>
      </article>
      {/* Challenge card */}
      <article className="challenge-card card pdv-shadow-sm pdv-hover-lift pdv-transition pdv-animate-slide-in-up" style={{ animationDelay: '400ms' }}>
        <div className="challenge-decoration"><div className="challenge-orbit orbit-a" /><div className="challenge-orbit orbit-b" /><span><Zap size={24} fill="currentColor" /></span></div>
        <div className="challenge-content"><div className="card-kicker">DAILY CHALLENGE <span className="new-pill">5 MIN</span></div><h3>Sharpen your<br />reasoning edge.</h3><p>5 questions · Mixed difficulty</p><Link className="challenge-link pdv-hover-lift pdv-transition-colors" to="/tests">Explore practice <ArrowRight size={16} /></Link></div>
      </article>
      {/* Courses section */}
      <section className="courses-section pdv-animate-fade-in" style={{ animationDelay: '500ms' }}>
        <div className="section-heading"><div><p className="eyebrow">CURATED FOR YOUR GOALS</p><h2>{t.courses}</h2></div><Link to="/learn" className="text-link pdv-hover-lift pdv-transition-colors">Explore library <ArrowRight size={15} /></Link></div>
        {courseQuery.isPending ? <div className="course-row" aria-label={t.courses} aria-busy="true">{[0, 1, 2].map((item) => <div key={item} className="phase6-skeleton" />)}</div>
          : courseQuery.isError ? <div className="empty-state card" role="alert"><p>{courseQuery.error.message}</p><button className="button button-secondary" onClick={() => void courseQuery.refetch()}>Try again</button></div>
          : courses.length === 0 ? <div className="empty-state card"><BookOpen className="empty-icon" size={28} /><h2>No courses available yet</h2><p>Check back when courses are added to your learning library.</p></div>
          : <div className="course-row pdv-grid pdv-gap-4">
            {courses.slice(0, 3).map((course, index) => <CourseCard key={course.id} course={course} index={index} style={{ animationDelay: `${100 + index * 100}ms` }} />)}
          </div>}
      </section>

      {/* Upcoming test card */}
      <article className="upcoming-card card pdv-shadow-sm pdv-hover-lift pdv-transition pdv-animate-slide-in-up" style={{ animationDelay: '600ms' }}>
        <div className="section-heading compact"><div><p className="eyebrow">STAY AHEAD</p><h2>{t.upcoming}</h2></div><span className="calendar-badge">{new Date().getFullYear()}</span></div>
        <Link to="/tests" className="upcoming-empty pdv-hover-lift pdv-transition-colors"><span className="calendar-icon"><Trophy size={20} /></span><div><b>{nextTest ? pickText(language, nextTest.title, nextTest.title_hi) : t.nextTestFallback}</b><p>{nextTest ? `${nextTest.total_questions} ${t.questionsCount} · ${nextTest.duration_minutes} ${t.minutes}` : testsQuery.isError ? (language === 'hi' ? 'टेस्ट लोड नहीं हो सके।' : 'Tests could not be loaded.') : t.nextTestFallbackBody}</p></div><ArrowRight size={16} /></Link>
      </article>
    </div>
  </AppShell>
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string | number }) {
  return <div className="performance-metric pdv-rounded-md pdv-p-3 pdv-bg-surface pdv-border pdv-hover-bg pdv-transition-colors"><span className="metric-label pdv-flex pdv-items-center pdv-gap-2 pdv-mb-2"><span className="stat-icon pdv-bg-blue-soft pdv-text-blue pdv-rounded pdv-p-1-5">{icon}</span><span className="pdv-text-xs pdv-font-semibold pdv-text-muted pdv-uppercase">{label}</span></span><strong className="pdv-text-lg pdv-font-bold">{value}</strong></div>
}

function CourseCard({ course, index, style }: { course: Course; index: number; style?: React.CSSProperties }) {
  const themes = ['course-art-lilac', 'course-art-blue', 'course-art-mint']
  const theme = themes[index % themes.length]
  const themeColor = theme === 'course-art-lilac' ? 'var(--purple)' : theme === 'course-art-blue' ? 'var(--blue)' : 'var(--mint)'
  return <article className="course-card card pdv-shadow-sm pdv-hover-lift pdv-transition pdv-animate-scale-in" style={{ ...style, animationDelay: style?.animationDelay || '0ms' }}>
    <div className={`course-art ${theme}`} style={{ borderColor: themeColor }}>
      <span className="course-art-mark">{['01', '02', '03'][index]}</span>
      <span className="course-art-orbit" />
      <span className="course-art-name">{course.title.split(':')[0]}</span>
      <span className="course-subject">{course.level}</span>
    </div>
    <div className="course-card-body">
      <div className="course-meta pdv-flex pdv-justify-between pdv-items-center pdv-mb-3">
        <span className="pdv-text-xs pdv-font-semibold pdv-text-muted">{course.total_lessons} LESSONS</span>
        {course.estimated_hours !== null && <span className="pdv-flex pdv-items-center pdv-gap-1 pdv-text-xs pdv-font-medium pdv-text-muted"><Clock3 size={12} /> {course.estimated_hours}H</span>}
      </div>
      <h3 className="pdv-text-lg pdv-font-bold pdv-mb-2">{course.title}</h3>
      <p className="pdv-text-sm pdv-text-muted pdv-mb-4 pdv-line-clamp-2">{course.description || 'A structured learning path to help you make steady progress.'}</p>
      <Link to="/learn" className="course-continue pdv-btn-primary pdv-w-full pdv-justify-center">Browse course <ArrowRight size={14} /></Link>
    </div>
  </article>
}
