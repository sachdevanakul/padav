import { lazy, Suspense, useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import AppShell from '../layouts/AppShell'
import AuthPage from '../pages/AuthPage'
import ExamSelectionPage from '../pages/ExamSelectionPage'
import OnboardingPage from '../pages/OnboardingPage'
import PlannerPage from '../pages/PlannerPage'
import { preferencesStore } from '../store/preferences'

const DashboardPage = lazy(() => import('../pages/DashboardPage'))

function WorkspacePage({ title }: { title: string }) {
  return <AppShell><section className="page-heading"><p className="eyebrow">PADAV WORKSPACE</p><h1>{title}</h1><p className="muted">This part of your learning workspace is being prepared.</p></section><div className="empty-state card"><span className="empty-icon">✦</span><h2>Good things are taking shape</h2><p>We’re connecting this space to your learning data. Your dashboard and exam setup are ready to use now.</p></div></AppShell>
}

export default function App() {
  const theme = preferencesStore((state) => state.theme)
  const language = preferencesStore((state) => state.language)
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.lang = language
  }, [theme, language])

  return <Routes>
    <Route path="/onboarding" element={<OnboardingPage />} />
    <Route path="/auth/login" element={<AuthPage mode="login" />} />
    <Route path="/auth/register" element={<AuthPage mode="register" />} />
    <Route path="/exams" element={<ExamSelectionPage />} />
    <Route path="/planner" element={<PlannerPage />} />
    <Route path="/" element={<Suspense fallback={<div className="page-loading">Loading your dashboard…</div>}><DashboardPage /></Suspense>} />
    <Route path="/learn" element={<WorkspacePage title="Learning library" />} />
    <Route path="/tests" element={<WorkspacePage title="Test arena" />} />
    <Route path="/analytics" element={<WorkspacePage title="Your analytics" />} />
    <Route path="/bookmarks" element={<WorkspacePage title="Your bookmarks" />} />
    <Route path="/profile" element={<WorkspacePage title="Your profile" />} />
    <Route path="/settings" element={<WorkspacePage title="Settings" />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
}
