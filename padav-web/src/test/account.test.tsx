import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../app/App'
import { authStore } from '../store/auth'
import { preferencesStore } from '../store/preferences'
import { currentWeekKeys, localDateKey } from '../lib/dates'
import { validateProfile } from '../pages/ProfilePage'
import { validatePasswordChange } from '../pages/SettingsPage'
import { translations } from '../locales/translations'

const USER = { id: 'u1', email: 'nakul@example.com', full_name: 'Nakul', avatar_url: null, is_active: true, is_verified: false, language: 'en', theme: 'dark', created_at: '2026-01-05T00:00:00' }
const PROFILE = { id: 'p1', user_id: 'u1', phone: null, date_of_birth: null, education_level: null, target_exams: null, study_goal_hours_per_week: null }
const TEST = { id: 't1', exam_id: 'e1', title: 'Practice Test 1', title_hi: null, description: null, description_hi: null, total_questions: 20, duration_minutes: 30, total_marks: 40, passing_marks: 0, negative_marks_per_question: 0.5, is_free: true }

type Call = { method: string; url: string; body: unknown }
function mockApi(routes: Record<string, unknown | ((call: Call) => unknown)>) {
  const calls: Call[] = []
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = String(input).replace('/api/v1', '')
    const method = (init.method ?? 'GET').toUpperCase()
    const call = { method, url, body: init.body ? JSON.parse(String(init.body)) : undefined }
    calls.push(call)
    const key = `${method} ${url.split('?')[0]}`
    if (!(key in routes)) return new Response(JSON.stringify({ detail: `unmocked ${key}` }), { status: 404 })
    const value = routes[key]
    const data = typeof value === 'function' ? (value as (c: Call) => unknown)(call) : value
    return new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } })
  }))
  return calls
}
function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}><App /></MemoryRouter></QueryClientProvider>)
}

beforeEach(() => {
  localStorage.clear(); authStore.getState().clear(); authStore.getState().setTokens('access', 'refresh'); authStore.getState().setUser(USER)
  preferencesStore.setState({ language: 'en', theme: 'dark' })
})
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

const base = { 'GET /users/me': USER, 'GET /users/me/profile': PROFILE, 'GET /exams': [], 'GET /users/me/exams': [] }

describe('validation', () => {
  const t = translations.en
  it('mirrors server profile rules', () => {
    const ok = { fullName: 'A', phone: '+91 98765-43210', dob: '2000-01-01', education: '', goal: '10' }
    expect(validateProfile(ok, t)).toEqual({})
    expect(validateProfile({ ...ok, fullName: ' ' }, t).fullName).toBeTruthy()
    expect(validateProfile({ ...ok, phone: 'abc' }, t).phone).toBeTruthy()
    expect(validateProfile({ ...ok, dob: '2999-01-01' }, t).dob).toBeTruthy()
    expect(validateProfile({ ...ok, goal: '169' }, t).goal).toBeTruthy()
    expect(validateProfile({ ...ok, goal: '1.5' }, t).goal).toBeTruthy()
  })
  it('checks password rules', () => {
    expect(validatePasswordChange({ current: 'oldpass123', next: 'newpass456', confirm: 'newpass456' }, t)).toEqual({})
    expect(validatePasswordChange({ current: 'x', next: 'short', confirm: 'short' }, t).next).toBeTruthy()
    expect(validatePasswordChange({ current: 'same-pass-1', next: 'same-pass-1', confirm: 'same-pass-1' }, t).next).toBeTruthy()
    expect(validatePasswordChange({ current: 'x', next: 'newpass456', confirm: 'other' }, t).confirm).toBeTruthy()
    expect(validatePasswordChange({ current: 'x', next: 'é'.repeat(37), confirm: 'é'.repeat(37) }, t).next).toBeTruthy()
  })
  it('builds a Monday-first week', () => {
    const keys = currentWeekKeys(new Date(2026, 10, 12))
    expect(keys).toHaveLength(7)
    expect(keys[0]).toBe('2026-11-09')
    expect(keys[6]).toBe('2026-11-15')
    expect(localDateKey(new Date(2026, 0, 5))).toBe('2026-01-05')
  })
})

describe('profile page', () => {
  it('loads and saves details', async () => {
    const u = userEvent.setup()
    const calls = mockApi({ ...base, 'PUT /users/me/profile': PROFILE, 'PUT /users/me': { ...USER, full_name: 'Nakul S' } })
    renderAt('/profile')
    const name = await screen.findByLabelText(/full name/i)
    expect(name).toHaveValue('Nakul')
    await u.clear(name); await u.type(name, 'Nakul S')
    await u.type(screen.getByLabelText(/phone/i), '+91 98765 43210')
    await u.type(screen.getByLabelText(/study hours|goal/i), '12')
    await u.click(screen.getByRole('button', { name: /save changes/i }))
    await waitFor(() => expect(calls.find((c) => c.method === 'PUT' && c.url === '/users/me/profile')?.body).toEqual({ phone: '+91 98765 43210', date_of_birth: null, education_level: null, study_goal_hours_per_week: 12 }))
    await waitFor(() => expect(calls.find((c) => c.method === 'PUT' && c.url === '/users/me')?.body).toEqual({ full_name: 'Nakul S' }))
    expect(await screen.findByRole('status')).toBeInTheDocument()
    expect(authStore.getState().user?.full_name).toBe('Nakul S')
  })

  it('blocks the API call on an invalid phone', async () => {
    const u = userEvent.setup()
    const calls = mockApi({ ...base, 'PUT /users/me/profile': PROFILE })
    renderAt('/profile')
    await u.type(await screen.findByLabelText(/phone/i), 'abc')
    await u.click(screen.getByRole('button', { name: /save changes/i }))
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'PUT')).toBe(false)
  })
})

describe('settings page', () => {
  it('rejects a mismatched confirmation without calling the API', async () => {
    const u = userEvent.setup()
    const calls = mockApi(base)
    renderAt('/settings')
    await u.type(await screen.findByLabelText(/current password/i), 'oldpass123')
    await u.type(screen.getByLabelText(/^new password/i), 'newpass456')
    await u.type(screen.getByLabelText(/confirm new password/i), 'different1')
    await u.click(screen.getByRole('button', { name: /update password/i }))
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(calls.some((c) => c.url === '/auth/change-password')).toBe(false)
  })

  it('changes the password and stores the new tokens', async () => {
    const u = userEvent.setup()
    const calls = mockApi({ ...base, 'POST /auth/change-password': { access_token: 'a2', refresh_token: 'r2', token_type: 'bearer' } })
    renderAt('/settings')
    await u.type(await screen.findByLabelText(/current password/i), 'oldpass123')
    await u.type(screen.getByLabelText(/^new password/i), 'newpass456')
    await u.type(screen.getByLabelText(/confirm new password/i), 'newpass456')
    await u.click(screen.getByRole('button', { name: /update password/i }))
    await waitFor(() => expect(calls.find((c) => c.url === '/auth/change-password')?.body).toEqual({ current_password: 'oldpass123', new_password: 'newpass456' }))
    await waitFor(() => expect(authStore.getState().refreshToken).toBe('r2'))
    expect(authStore.getState().accessToken).toBe('a2')
  })

  it('switches language immediately and syncs best-effort', async () => {
    const u = userEvent.setup()
    const calls = mockApi({ ...base, 'PUT /users/me': USER })
    renderAt('/settings')
    await u.click(await screen.findByRole('radio', { name: 'हिन्दी' }))
    expect(preferencesStore.getState().language).toBe('hi')
    expect(await screen.findByRole('heading', { name: translations.hi.settingsTitle })).toBeInTheDocument()
    await waitFor(() => expect(calls.find((c) => c.method === 'PUT' && c.url === '/users/me')?.body).toEqual({ language: 'hi' }))
  })
})

describe('dashboard', () => {
  const overview = { total_tests_taken: 1, average_score: 50, overall_accuracy: 50, total_study_hours: 1, current_streak: 2, total_questions_attempted: 5, active_dates: [localDateKey(new Date())] }
  const dash = { ...base, 'GET /users/me/exams': [{ id: 'm1', exam_id: 'e1', is_primary: true }], 'GET /courses': [], 'GET /analytics/overview': overview, 'GET /tests': [TEST], 'GET /bookmarks': [] }

  it('shows an empty-trend message, no fake data, and links the next test', async () => {
    mockApi({ ...dash, 'GET /analytics/trends': [] })
    renderAt('/')
    expect(await screen.findByText(translations.en.trendEmpty, { selector: 'p.chart-empty' })).toBeInTheDocument()
    expect(document.body.textContent).not.toMatch(/sample weekly trend/i)
    const link = (await screen.findByText('Practice Test 1')).closest('a')!
    expect(link).toHaveAttribute('href', '/tests')
  })

  it('sends the timezone offset with the overview request', async () => {
    const calls = mockApi({ ...dash, 'GET /analytics/trends': [] })
    renderAt('/')
    await waitFor(() => expect(calls.some((c) => c.url.startsWith('/analytics/overview?tz_offset='))).toBe(true))
  })
})
