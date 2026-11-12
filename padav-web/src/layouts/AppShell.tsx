import type { ReactNode } from 'react'
import { useEffect, useState, useCallback } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  Activity,
  Bell,
  Bookmark,
  BookOpen,
  Brain,
  CalendarDays,
  ChevronDown,
  Command,
  GraduationCap,
  Home,
  LogOut,
  Moon,
  Search,
  Settings,
  Sun,
  Target,
  UserRound,
  Menu,
} from 'lucide-react'
import { preferencesStore } from '../store/preferences'
import { Button } from '../components/ui/Button'
import { authStore } from '../store/auth'
import { api } from '../services/api'
import { translations } from '../locales/translations'

const links = [
  { to: '/', key: 'home', icon: Home },
  { to: '/learn', key: 'learn', icon: BookOpen },
  { to: '/planner', key: 'planner', icon: CalendarDays },
  { to: '/tests', key: 'tests', icon: Target },
  { to: '/pia', key: 'pia', icon: Brain },
  { to: '/analytics', key: 'analytics', icon: Activity },
  { to: '/bookmarks', key: 'bookmarks', icon: Bookmark },
]

export default function AppShell({ children }: { children: ReactNode }) {
  const { language, theme, toggleTheme, setLanguage } = preferencesStore()
  const { user, refreshToken, clear } = authStore()
  const navigate = useNavigate()
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [isThemeToggled, setIsThemeToggled] = useState(false)

  const handleDrawerOpen = useCallback(() => setIsDrawerOpen(true), [])
  const handleDrawerClose = useCallback(() => setIsDrawerOpen(false), [])
  const handleNavItemClick = useCallback(() => {
    if (isMobile) setIsDrawerOpen(false)
  }, [isMobile])
  const handleToggleCollapse = useCallback(() => {
    setIsSidebarCollapsed((prev) => !prev)
  }, [])
  const handleThemeToggle = useCallback(() => {
    toggleTheme()
    setIsThemeToggled((prev) => !prev)
  }, [toggleTheme])
  const handleLanguageToggle = useCallback(() => {
    setLanguage(language === 'en' ? 'hi' : 'en')
  }, [language, setLanguage])

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth <= 900)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isDrawerOpen) setIsDrawerOpen(false)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isDrawerOpen])

  useEffect(() => {
    if (isDrawerOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isDrawerOpen])

  useEffect(() => {
    if (!isMobile) {
      setIsDrawerOpen(false)
    }
  }, [isMobile])

  const t = translations[language]

  async function logout() {
    if (refreshToken) await api.logout(refreshToken).catch(() => undefined)
    clear()
    navigate('/auth/login')
  }

  return (
    <div className="app-frame pdv-transition">
      {/* Mobile drawer backdrop */}
      {isDrawerOpen && (
        <div
          className="pdv-drawer-backdrop pdv-animate-fade-in"
          onClick={handleDrawerClose}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') handleDrawerClose()
          }}
        />
      )}

      <aside
        className={`
          sidebar
          ${isMobile ? 'mobile-drawer' : ''}
          ${isDrawerOpen && isMobile ? 'drawer-open' : ''}
          ${isSidebarCollapsed && !isMobile ? 'sidebar-collapsed' : ''}
          pdv-transition
        `}
      >
        <div className="pdv-flex pdv-flex-col">
          <NavLink
            to="/"
            className="brand"
            onClick={handleNavItemClick}
          >
            <span className="brand-mark"><GraduationCap size={21} /></span>
            <span>
              PADAV<small>YOUR AMBITION. YOUR ADVANTAGE.</small>
            </span>
          </NavLink>

          {!isSidebarCollapsed && <div className="side-label">LEARNING SPACE</div>}

          <nav className="side-nav" aria-label="Main navigation">
            {links.map(({ to, key, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `nav-item ${isActive ? 'active' : ''} ${isSidebarCollapsed ? 'nav-item-collapsed' : ''} pdv-hover-lift pdv-transition`
                }
                onClick={handleNavItemClick}
              >
                <Icon size={18} strokeWidth={1.8} className="pdv-transition-transform" />
                {!isSidebarCollapsed && <span>{t[key]}</span>}
                {key === 'home' && <span className="nav-dot" />}
              </NavLink>
            ))}
          </nav>

          {!isSidebarCollapsed && (
            <div className="side-label side-label-bottom">ACCOUNT</div>
          )}

          <nav className="side-nav">
            <NavLink
              to="/profile"
              className={({ isActive }) =>
                `nav-item ${isActive ? 'active' : ''} ${isSidebarCollapsed ? 'nav-item-collapsed' : ''} pdv-hover-lift pdv-transition`
              }
              onClick={handleNavItemClick}
            >
              <UserRound size={18} />
              {!isSidebarCollapsed && <span>{t.profile}</span>}
            </NavLink>
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `nav-item ${isActive ? 'active' : ''} ${isSidebarCollapsed ? 'nav-item-collapsed' : ''} pdv-hover-lift pdv-transition`
              }
              onClick={handleNavItemClick}
            >
              <Settings size={18} />
              {!isSidebarCollapsed && <span>{t.settings}</span>}
            </NavLink>
          </nav>

          <div className="sidebar-spacer" />

          {!isSidebarCollapsed && (
            <div className="sidebar-goal pdv-card pdv-shadow-sm pdv-p-4">
              <span className="goal-orbit"><Target size={19} /></span>
              <div>
                <strong>Small steps. Big ranks.</strong>
                <p>Your next study session is one decision away.</p>
              </div>
            </div>
          )}

          {user ? (
            <button
              className="user-card pdv-hover-bg pdv-transition-colors pdv-focus-ring"
              onClick={logout}
            >
              <span className="avatar">{user.full_name?.slice(0, 1) || 'P'}</span>
              {!isSidebarCollapsed && (
                <span className="user-name">
                  {user.full_name || user.email}
                  <small>Student account</small>
                </span>
              )}
              {!isSidebarCollapsed && <LogOut size={16} />}
            </button>
          ) : (
            <NavLink
              className="user-card sign-in-card pdv-hover-bg pdv-transition-colors pdv-focus-ring"
              to="/auth/login"
              onClick={handleNavItemClick}
            >
              <span className="avatar"><UserRound size={17} /></span>
              {!isSidebarCollapsed && (
                <span className="user-name">
                  Sign in<small>Sync your learning</small>
                </span>
              )}
              {!isSidebarCollapsed && <ChevronDown size={16} />}
            </NavLink>
          )}

          {!isMobile && !isSidebarCollapsed && (
            <Button
              variant="ghost"
              aria-label="Collapse sidebar"
              onClick={handleToggleCollapse}
            >
              <ChevronDown size={16} />
            </Button>
          )}
        </div>
      </aside>
    <div className="main-column pdv-transition">
      <header className="topbar pdv-shadow-sm pdv-transition-colors">
        <div className="mobile-brand">
          <span className="brand-mark"><GraduationCap size={19} /></span>
          <b>PADAV</b>
        </div>

        {!isMobile && (
          <label className="global-search pdv-hover-bg pdv-transition-colors pdv-focus-ring">
            <Search size={17} />
            <input
              aria-label="Search"
              placeholder={t.search}
              className="pdv-focus-ring"
            />
            <kbd><Command size={11} /> K</kbd>
          </label>
        )}

        <div className="top-actions pdv-flex pdv-items-center pdv-gap-2">
          <Button
            variant="ghost"
            aria-label="Change language"
            onClick={handleLanguageToggle}
          >
            {language === 'en' ? 'HI' : 'EN'}
          </Button>

          <Button
            variant="ghost"
            aria-label="Toggle theme"
            onClick={handleThemeToggle}
          >
            <span className={`theme-toggle-icon ${isThemeToggled ? 'rotated' : ''}`}>
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </span>
          </Button>

          <Button
            variant="ghost"
            aria-label="Notifications"
            data-count="3"
          >
            <Bell size={18} />
            <i />
          </Button>

          {isMobile ? (
            <Button
              variant="ghost"
              aria-label="Open navigation"
              onClick={handleDrawerOpen}
            >
              <Menu size={18} />
            </Button>
          ) : (
            <Button
              variant="ghost"
              aria-label="Open profile"
              onClick={() => navigate('/profile')}
            >
              {user?.full_name?.slice(0, 1) || 'A'}
            </Button>
          )}
        </div>
      </header>

      <main className="workspace">{children}</main>

      <nav className="mobile-nav pdv-transition-colors" aria-label="Mobile navigation">
        {links.slice(0, 5).map(({ to, key, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            aria-label={t[key]}
            className={({ isActive }) => isActive ? 'mobile-nav-link active' : 'mobile-nav-link'}
            onClick={handleNavItemClick}
          >
            <Icon size={19} />
            <small>{t[key]}</small>
          </NavLink>
        ))}
      </nav>
    </div>
  </div>
  )
}
