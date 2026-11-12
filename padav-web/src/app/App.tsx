import { lazy, Suspense, useEffect } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import AppShell from '../layouts/AppShell'
import AnalyticsPage from '../pages/AnalyticsPage'
import AuthPage from '../pages/AuthPage'
import ExamSelectionPage from '../pages/ExamSelectionPage'
import OnboardingPage from '../pages/OnboardingPage'
import PlannerPage from '../pages/PlannerPage'
import TestsPage from '../pages/TestsPage'
import ProfilePage from '../pages/ProfilePage'
import SettingsPage from '../pages/SettingsPage'
import { api } from '../services/api'
import { authStore } from '../store/auth'
import { preferencesStore } from '../store/preferences'
import ToastProvider from '../components/ui/Toast'

const DashboardPage = lazy(() => import('../pages/DashboardPage'))
const TestRunnerPage = lazy(() => import('../pages/TestRunnerPage'))
const TestResultPage = lazy(() => import('../pages/TestResultPage'))

function WorkspacePage({ title }: { title: string }) {
  return <AppShell><section className="page-heading"><p className="eyebrow">PADAV WORKSPACE</p><h1>{title}</h1><p className="muted">This part of your learning workspace is being prepared.</p></section><div className="empty-state card"><span className="empty-icon">✦</span><h2>Good things are taking shape</h2><p>We’re connecting this space to your learning data. Your dashboard and exam setup are ready to use now.</p></div></AppShell>
}

function HomeRoute() {
  const token = authStore((state) => state.accessToken)
  const hasCompletedOnboarding = localStorage.getItem('padav-onboarded') === 'true'
  const examsQuery = useQuery({ queryKey: ['my-exams'], queryFn: api.myExams, enabled: Boolean(token) })

  if (!token) return <Navigate to={hasCompletedOnboarding ? '/auth/login' : '/onboarding'} replace />
  if (token && examsQuery.isPending) return <div className="page-loading">Loading your workspace…</div>
  if (token && examsQuery.isError) {
    return <div className="page-loading" role="alert">Couldn’t load your exam preferences. <button onClick={() => examsQuery.refetch()}>Try again</button></div>
  }
  if (token && examsQuery.data?.length === 0) return <Navigate to="/exams" replace />

  return <Suspense fallback={<div className="page-loading">Loading your dashboard…</div>}><DashboardPage /></Suspense>
}

function RequireAuth() {
  const token = authStore((state) => state.accessToken)
  const location = useLocation()
  return token ? <Outlet /> : <Navigate to="/auth/login" replace state={{ from: location }} />
}

export default function App() {
  const theme = preferencesStore((state) => state.theme)
  const language = preferencesStore((state) => state.language)
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.lang = language
  }, [theme, language])

  return <ToastProvider><Routes>
    <Route path="/onboarding" element={<OnboardingPage />} />
    <Route path="/auth/login" element={<AuthPage mode="login" />} />
    <Route path="/auth/register" element={<AuthPage mode="register" />} />
    <Route path="/" element={<HomeRoute />} />
    <Route element={<RequireAuth />}>
      <Route path="/exams" element={<ExamSelectionPage />} />
      <Route path="/planner" element={<PlannerPage />} />
      <Route path="/learn" element={<WorkspacePage title="Learning library" />} />
      <Route path="/tests" element={<TestsPage />} />
      <Route path="/tests/attempts/:attemptId" element={<Suspense fallback={<div className="page-loading">Preparing your test…</div>}><TestRunnerPage /></Suspense>} />
      <Route path="/tests/attempts/:attemptId/result" element={<Suspense fallback={<div className="page-loading">Loading your result…</div>}><TestResultPage /></Suspense>} />
      <Route path="/analytics" element={<AnalyticsPage />} />
      <Route path="/bookmarks" element={<WorkspacePage title="Your bookmarks" />} />
      <Route path="/profile" element={<ProfilePage />} />
      <Route path="/settings" element={<SettingsPage />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></ToastProvider>
}
