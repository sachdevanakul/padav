import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../app/App'
import { authStore } from '../store/auth'

function renderApp(initialEntry = '/onboarding') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[initialEntry]}><App /></MemoryRouter></QueryClientProvider>)
}

beforeEach(() => {
  localStorage.clear()
  authStore.getState().clear()
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('onboarding experience', () => {
  it('moves through the three preparation steps', async () => {
    const user = userEvent.setup()
    renderApp()
    expect(screen.getByRole('heading', { name: /learn smart/i })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /continue/i }))
    expect(await screen.findByRole('heading', { name: /prepare\.\s*practice/i })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /continue/i }))
    await waitFor(() => expect(screen.getAllByRole('heading').map((heading) => heading.textContent).join(' ')).toMatch(/your success/i))
    expect(screen.getByRole('button', { name: /start your journey/i })).toBeInTheDocument()
  })

  it('sends a first-time visitor at the root to onboarding', () => {
    renderApp('/')
    expect(screen.getByRole('heading', { name: /learn smart/i })).toBeInTheDocument()
  })

  it('sends visitors who skip onboarding to sign in', async () => {
    const user = userEvent.setup()
    renderApp('/')
    await user.click(screen.getByRole('button', { name: /skip for now/i }))
    expect(await screen.findByRole('heading', { name: /good to see you again/i })).toBeInTheDocument()
  })

  it('continues from onboarding to account registration', async () => {
    const user = userEvent.setup()
    renderApp('/')
    await user.click(screen.getByRole('button', { name: /continue/i }))
    await user.click(screen.getByRole('button', { name: /continue/i }))
    await user.click(screen.getByRole('button', { name: /start your journey/i }))
    expect(await screen.findByRole('heading', { name: /create your account/i })).toBeInTheDocument()
  })

  it('requires sign-in for protected pages', async () => {
    renderApp('/planner')
    expect(await screen.findByRole('heading', { name: /good to see you again/i })).toBeInTheDocument()
  })

  it('prompts a signed-in user with no saved exams to choose goals', async () => {
    authStore.getState().setTokens('access', 'refresh')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, status: 200, json: async () => [],
    }))
    renderApp('/')
    expect(await screen.findByRole('heading', { name: /which exams are\s*you preparing for/i })).toBeInTheDocument()
  })

  it('opens the dashboard for a signed-in user with saved exams', async () => {
    authStore.getState().setTokens('access', 'refresh')
    authStore.getState().setUser({
      id: 'user-1', email: 'student@example.com', full_name: 'Student', avatar_url: null,
      is_active: true, is_verified: true, language: 'en', theme: 'dark', created_at: '',
    })
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => Promise.resolve({
      ok: true,
      status: 200,
      json: async () => String(input).endsWith('/users/me/exams')
        ? [{ id: 'preference-1', exam_id: 'exam-1', is_primary: true }]
        : [],
    })))
    renderApp('/')
    expect(await screen.findByRole('heading', { name: /good morning|good afternoon|good evening/i })).toBeInTheDocument()
  })

  it('uses saved account exams when reopening exam selection', async () => {
    authStore.getState().setTokens('access', 'refresh')
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => Promise.resolve({
      ok: true,
      status: 200,
      json: async () => String(input).endsWith('/users/me/exams')
        ? [{ id: 'preference-1', exam_id: 'exam-1', is_primary: true }]
        : String(input).endsWith('/exams')
          ? [{ id: 'exam-1', name: 'SSC CGL', name_hi: null, code: 'SSC-CGL', category: 'SSC', description: null, description_hi: null, is_active: true, created_at: '' }]
          : [],
    })))
    renderApp('/exams')
    expect(await screen.findByRole('button', { name: /SSC CGL/i })).toHaveAttribute('aria-pressed', 'true')
  })
})
