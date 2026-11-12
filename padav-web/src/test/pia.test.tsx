import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../app/App'
import { authStore } from '../store/auth'
import { preferencesStore } from '../store/preferences'
import { validateConsent } from '../pages/PiaPage'
import { translations } from '../locales/translations'

const USER = { id: 'u1', email: 'n@example.com', full_name: 'Nakul', avatar_url: null, is_active: true, is_verified: false, language: 'en', theme: 'dark', created_at: '2026-01-05T00:00:00' }
const run = (over: Record<string, unknown>) => ({ domain: 'gf', label: 'Fluid reasoning (Gf)', description: 'x', sequence: 1, status: 'pending', question_count: 2, time_limit_seconds: 480, seconds_remaining: null, ...over })
const session = (runs: unknown[], over: Record<string, unknown> = {}) => ({ id: 's1', status: 'in_progress', language: 'en', created_at: '2026-11-12T00:00:00', completed_at: null, total_questions: 50, total_minutes: 46, runs, ...over })
const ITEMS = [
  { item_code: 'PIA-GF-SQ-001', position: 1, stem: 'What comes next? 3, 6, 12, ?', options: [{ key: 'a', text: '18' }, { key: 'b', text: '24' }], stimulus_type: 'text', asset_id: null, selected_key: null },
  { item_code: 'PIA-GF-SQ-002', position: 2, stem: 'Second question?', options: [{ key: 'a', text: 'x' }, { key: 'b', text: 'y' }], stimulus_type: 'text', asset_id: null, selected_key: 'b' },
]
const REPORT = {
  session_id: 's1', status: 'experimental', form_code: 'PIA-MASTER', form_version: 1, scoring_model_version: 'raw-v1', norm_version: null,
  total_questions: 50, total_correct: 31, total_omitted: 4, raw_accuracy: 0.62, notices: ['Experimental research result. This is not a validated or standardized IQ score.'],
  created_at: '2026-11-12T01:00:00',
  domains: [{ domain: 'gf', label: 'Fluid reasoning (Gf)', questions: 10, correct: 10, omitted: 0, accuracy: 1, median_response_ms: null, timed_out: false, interrupted: false },
    { domain: 'glr', label: 'Long-term retrieval (Glr)', questions: 4, correct: 0, omitted: 4, accuracy: 0, median_response_ms: null, timed_out: true, interrupted: true }],
}

type Call = { method: string; url: string; body: unknown }
function mockApi(routes: Record<string, unknown | ((c: Call) => Response | unknown)>) {
  const calls: Call[] = []
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = String(input).replace('/api/v1', '')
    const method = (init.method ?? 'GET').toUpperCase()
    const call = { method, url, body: init.body ? JSON.parse(String(init.body)) : undefined }
    calls.push(call)
    const key = `${method} ${url}`
    if (!(key in routes)) return new Response(JSON.stringify({ detail: `unmocked ${key}` }), { status: 404 })
    const value = routes[key]
    const data = typeof value === 'function' ? (value as (c: Call) => unknown)(call) : value
    if (data instanceof Response) return data
    return new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } })
  }))
  return calls
}
const fail = (status: number, detail: string) => new Response(JSON.stringify({ detail }), { status })
function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}><App /></MemoryRouter></QueryClientProvider>)
}

beforeEach(() => {
  localStorage.clear(); authStore.getState().clear(); authStore.getState().setTokens('a', 'r'); authStore.getState().setUser(USER)
  preferencesStore.setState({ language: 'en', theme: 'dark' })
})
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

const shell = { 'GET /users/me': USER, 'GET /users/me/exams': [{ id: 'm', exam_id: 'e', is_primary: true }], 'GET /exams': [] }

describe('consent validation', () => {
  const t = translations.en
  it('enforces the age and guardian rules', () => {
    expect(validateConsent({ age: '25', guardian: false, accepted: true }, t)).toEqual({})
    expect(validateConsent({ age: '12', guardian: true, accepted: true }, t).age).toBeTruthy()
    expect(validateConsent({ age: '', guardian: false, accepted: true }, t).age).toBeTruthy()
    expect(validateConsent({ age: '15', guardian: false, accepted: true }, t).guardian).toBeTruthy()
    expect(validateConsent({ age: '15', guardian: true, accepted: true }, t)).toEqual({})
    expect(validateConsent({ age: '25', guardian: false, accepted: false }, t).accepted).toBeTruthy()
  })
})

describe('intro and consent', () => {
  it('shows the experimental notice and resumes without asking consent again', async () => {
    const u = userEvent.setup()
    const calls = mockApi({ ...shell, 'POST /pia/sessions': session([run({})]), 'GET /pia/sessions/s1': session([run({})]) })
    renderAt('/pia')
    expect(await screen.findByRole('note')).toHaveTextContent(/not a validated or standardized IQ/i)
    await u.click(screen.getByRole('button', { name: /begin or resume/i }))
    expect(await screen.findByRole('heading', { name: /1\. Fluid reasoning/i })).toBeInTheDocument()
    expect(calls.some((c) => c.url === '/pia/consent')).toBe(false)
  })

  it('asks for consent when the server requires it, then starts', async () => {
    const u = userEvent.setup()
    let consented = false
    const calls = mockApi({
      ...shell,
      'POST /pia/consent': () => { consented = true; return { id: 'c1' } },
      'POST /pia/sessions': () => (consented ? session([run({})]) : fail(403, 'Consent is required')),
      'GET /pia/sessions/s1': session([run({})]),
    })
    renderAt('/pia')
    await u.click(await screen.findByRole('button', { name: /begin or resume/i }))
    await u.type(await screen.findByLabelText(/your age/i), '15')
    await u.click(screen.getByLabelText(/agree to take part/i))
    await u.click(screen.getByRole('button', { name: /agree and begin/i }))
    expect(await screen.findAllByRole('alert')).not.toHaveLength(0) // guardian consent missing
    expect(calls.some((c) => c.url === '/pia/consent')).toBe(false)
    await u.click(screen.getByLabelText(/parent or guardian/i))
    await u.click(screen.getByRole('button', { name: /agree and begin/i }))
    await waitFor(() => expect(calls.find((c) => c.url === '/pia/consent')?.body).toEqual({ accepted: true, age: 15, guardian_consent: true }))
    expect(await screen.findByRole('heading', { name: /1\. Fluid reasoning/i })).toBeInTheDocument()
  })
})

describe('session overview and runner', () => {
  it('only offers the next section and starts it', async () => {
    const u = userEvent.setup()
    let started = false
    const calls = mockApi({
      ...shell,
      'GET /pia/sessions/s1': () => session(started
        ? [run({ status: 'in_progress', seconds_remaining: 470 }), run({ domain: 'gc', label: 'Verbal', sequence: 2 })]
        : [run({}), run({ domain: 'gc', label: 'Verbal', sequence: 2 })]),
      'POST /pia/sessions/s1/subtests/gf/start': () => { started = true; return ITEMS },
    })
    renderAt('/pia/sessions/s1')
    expect(await screen.findAllByRole('button', { name: /start section/i })).toHaveLength(1) // gc stays locked
    await u.click(screen.getByRole('button', { name: /start section/i }))
    expect(await screen.findByText('What comes next? 3, 6, 12, ?')).toBeInTheDocument()
    expect(screen.getByRole('timer')).toHaveTextContent(/7:5\d|8:00/)
    expect(calls.filter((c) => c.url === '/pia/sessions/s1/subtests/gf/start')).toHaveLength(1)
    expect(document.body.textContent).not.toMatch(/correct answer/i)
  })

  it('saves answers with response time, shows saved answers on resume, and finishes via the server', async () => {
    const u = userEvent.setup()
    let done = false
    const calls = mockApi({
      ...shell,
      'GET /pia/sessions/s1': () => session([done ? run({ status: 'completed' }) : run({ status: 'in_progress', seconds_remaining: 300 })]),
      'GET /pia/sessions/s1/subtests/gf/items': ITEMS,
      'PUT /pia/sessions/s1/subtests/gf/answers': { saved: true, seconds_remaining: 290 },
      'POST /pia/sessions/s1/subtests/gf/complete': () => { done = true; return session([run({ status: 'completed' })]) },
    })
    renderAt('/pia/sessions/s1')
    await u.click(await screen.findByRole('radio', { name: /24/ }))
    await waitFor(() => expect(calls.find((c) => c.method === 'PUT')?.body).toMatchObject({ item_code: 'PIA-GF-SQ-001', selected_key: 'b' }))
    expect(typeof (calls.find((c) => c.method === 'PUT')?.body as { client_response_ms: number }).client_response_ms).toBe('number')
    expect(await screen.findByText(/all answers saved|saved/i)).toBeInTheDocument()
    await u.click(screen.getByRole('button', { name: /^next/i }))
    expect(screen.getByRole('radio', { name: /^B\s*y|y/ })).toBeChecked() // saved answer restored
    await u.click(screen.getByRole('button', { name: /finish section/i }))
    expect(await screen.findByText(/0 unanswered/i)).toBeInTheDocument()
    await u.click(screen.getAllByRole('button', { name: /finish section/i }).at(-1)!)
    await waitFor(() => expect(calls.some((c) => c.url.endsWith('/complete'))).toBe(true))
    expect(await screen.findByRole('button', { name: /see my results/i })).toBeInTheDocument()
  })

  it('treats a 409 from the server as time up and returns to the overview', async () => {
    const u = userEvent.setup()
    let expired = false
    mockApi({
      ...shell,
      'GET /pia/sessions/s1': () => session([expired ? run({ status: 'timed_out' }) : run({ status: 'in_progress', seconds_remaining: 300 })]),
      'GET /pia/sessions/s1/subtests/gf/items': ITEMS,
      'PUT /pia/sessions/s1/subtests/gf/answers': () => { expired = true; return fail(409, 'Time is up for this subtest') },
    })
    renderAt('/pia/sessions/s1')
    await u.click(await screen.findByRole('radio', { name: /24/ }))
    expect(await screen.findByText(/time ended/i, undefined, { timeout: 4000 })).toBeInTheDocument()
  })

  it('finishes the session and opens the report', async () => {
    const u = userEvent.setup()
    mockApi({
      ...shell,
      'GET /pia/sessions/s1': session([run({ status: 'completed' })]),
      'POST /pia/sessions/s1/finish': REPORT, 'GET /pia/sessions/s1/report': REPORT,
    })
    renderAt('/pia/sessions/s1')
    await u.click(await screen.findByRole('button', { name: /see my results/i }))
    expect(await screen.findByRole('heading', { name: /your assessment results/i })).toBeInTheDocument()
    expect(screen.getByText('31 / 50')).toBeInTheDocument()
    expect(screen.getByText('62%')).toBeInTheDocument()
    expect(screen.getByText(/raw accuracy is the share/i)).toBeInTheDocument()
    expect(screen.getByText(/time ran out/i)).toBeInTheDocument()
    expect(screen.getByText(/interrupted/i)).toBeInTheDocument()
    expect(document.body.textContent).not.toMatch(/\bIQ\s*(score)?\s*[:=]?\s*\d|percentile|gifted/i)
  })

  it('renders in Hindi', async () => {
    preferencesStore.setState({ language: 'hi' })
    mockApi({ ...shell, 'GET /pia/sessions/s1': session([run({})]) })
    renderAt('/pia/sessions/s1')
    expect(await screen.findByRole('heading', { name: new RegExp(translations.hi.piaDomain_gf) })).toBeInTheDocument()
  })
})
