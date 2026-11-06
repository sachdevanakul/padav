import type { ReactNode } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { Activity, Bell, Bookmark, BookOpen, CalendarDays, ChevronDown, Command, GraduationCap, Home, LogOut, Moon, Search, Settings, Sun, Target, UserRound } from 'lucide-react'
import { preferencesStore } from '../store/preferences'
import { authStore } from '../store/auth'
import { api } from '../services/api'
import { translations } from '../locales/translations'

const links = [
  { to: '/', key: 'home', icon: Home }, { to: '/learn', key: 'learn', icon: BookOpen }, { to: '/planner', key: 'planner', icon: CalendarDays },
  { to: '/tests', key: 'tests', icon: Target }, { to: '/analytics', key: 'analytics', icon: Activity },
  { to: '/bookmarks', key: 'bookmarks', icon: Bookmark },
]

export default function AppShell({ children }: { children: ReactNode }) {
  const { language, theme, toggleTheme, setLanguage } = preferencesStore()
  const { user, refreshToken, clear } = authStore()
  const navigate = useNavigate()
  const t = translations[language]

  async function logout() {
    if (refreshToken) await api.logout(refreshToken).catch(() => undefined)
    clear()
    navigate('/auth/login')
  }

  return <div className="app-frame">
    <aside className="sidebar">
      <NavLink to="/" className="brand"><span className="brand-mark"><GraduationCap size={21} /></span><span>PADAV<small>YOUR AMBITION. YOUR ADVANTAGE.</small></span></NavLink>
      <div className="side-label">LEARNING SPACE</div>
      <nav className="side-nav" aria-label="Main navigation">{links.map(({ to, key, icon: Icon }) => <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><Icon size={18} strokeWidth={1.8} /><span>{t[key]}</span>{key === 'home' && <span className="nav-dot" />}</NavLink>)}</nav>
      <div className="side-label side-label-bottom">ACCOUNT</div>
      <nav className="side-nav"><NavLink to="/profile" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><UserRound size={18} /><span>{t.profile}</span></NavLink><NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><Settings size={18} /><span>{t.settings}</span></NavLink></nav>
      <div className="sidebar-spacer" />
      <div className="sidebar-goal"><span className="goal-orbit"><Target size={19} /></span><div><strong>Small steps. Big ranks.</strong><p>Your next study session is one decision away.</p></div></div>
      {user ? <button className="user-card" onClick={logout}><span className="avatar">{user.full_name?.slice(0, 1) || 'P'}</span><span className="user-name">{user.full_name || user.email}<small>Student account</small></span><LogOut size={16} /></button> : <NavLink className="user-card sign-in-card" to="/auth/login"><span className="avatar"><UserRound size={17} /></span><span className="user-name">Sign in<small>Sync your learning</small></span><ChevronDown size={16} /></NavLink>}
    </aside>
    <div className="main-column">
      <header className="topbar">
        <div className="mobile-brand"><span className="brand-mark"><GraduationCap size={19} /></span><b>PADAV</b></div>
        <label className="global-search"><Search size={17} /><input aria-label="Search" placeholder={t.search} /><kbd><Command size={11} /> K</kbd></label>
        <div className="top-actions">
          <button className="icon-button lang-button" aria-label="Change language" onClick={() => setLanguage(language === 'en' ? 'hi' : 'en')}>{language === 'en' ? 'HI' : 'EN'}</button>
          <button className="icon-button" aria-label="Toggle theme" onClick={toggleTheme}>{theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}</button>
          <button className="icon-button notification-button" aria-label="Notifications"><Bell size={18} /><i /></button>
          <button className="top-avatar" aria-label="Open profile" onClick={() => navigate('/profile')}>{user?.full_name?.slice(0, 1) || 'A'}</button>
        </div>
      </header>
      <main className="workspace">{children}</main>
      <nav className="mobile-nav" aria-label="Mobile navigation">{links.slice(0, 5).map(({ to, key, icon: Icon }) => <NavLink key={to} to={to} end={to === '/'} aria-label={t[key]} className={({ isActive }) => isActive ? 'mobile-nav-link active' : 'mobile-nav-link'}><Icon size={19} /><small>{t[key]}</small></NavLink>)}</nav>
    </div>
  </div>
}
