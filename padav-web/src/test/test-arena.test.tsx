import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../app/App'
import { authStore } from '../store/auth'
import { formatClock, parseServerDate } from '../lib/dates'

const option = (qid: string, key: string, text: string) => ({ id: `${qid}-${key}`, key, text, text_hi: null })
const question = (id: string, text: string) => ({
  id, subject_id: 's', text, text_hi: null, difficulty: 'easy', marks: 2, negative_marks: 0.5,
  options: [option(id, 'b', 'Thirty-six'), option(id, 'a', 'Twenty-four'), option(id, 'c', 'Thirty')],
})
const QUESTIONS = [question('q1', 'What is 15% of 240?'), question('q2', 'Second question?')]
const attempt = (over: Record<string, unknown> = {}) => ({
  id: 'att1', test_id: 't1', test_title: 'Practice Test 1', status: 'in_progress', started_at: '2026-11-11T06:00:00',
  completed_at: null, total_questions: 2, attempted_questions: 0, correct_answers: 0, incorrect_answers: 0,
  unanswered_questions: 2, score_obtained: 0, max_score: 4, accuracy: 0, is_submitted: false,
  duration_minutes: 10, seconds_remaining: 600, answers: [], ...over,
})
const TEST = { id: 't1', exam_id: 'e1', title: 'Practice Test 1', title_hi: null, description: 'Warm-up', description_hi: null, total_questions: 2, duration_minutes: 10, total_marks: 4, passing_marks: 0, negative_marks_per_question: 0.5, is_free: true }
const SUBMITTED = attempt({ is_submitted: true, status: 'completed', seconds_remaining: null, correct_answers: 1, incorrect_answers: 1, unanswered_questions: 0, attempted_questions: 2, score_obtained: 1.5, accuracy: 50 })
const REVIEW = [
  { question: QUESTIONS[0], correct_option_key: 'b', selected_option_key: 'b', explanation: '240 x 15 / 100 = 36.', explanation_hi: null },
  { question: QUESTIONS[1], correct_option_key: 'b', selected_option_key: 'a', explanation: null, explanation_hi: null },
]

type Call = { method: string; url: string; body: unknown }
function mockApi(routes: Record<string, unknown | ((call: Call) => unknown)>) {
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
    return new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } })
  }))
  return calls
}

function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}><App /></MemoryRouter></QueryClientProvider>)
}

beforeEach(() => { localStorage.clear(); authStore.getState().clear(); authStore.getState().setTokens('access', 'refresh') })
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

describe('helpers', () => {
  it('reads server timestamps as UTC and formats the clock', () => {
    expect(parseServerDate('2026-11-11T06:00:00').toISOString()).toBe('2026-11-11T06:00:00.000Z')
    expect(parseServerDate('2026-11-11T06:00:00+05:30').toISOString()).toBe('2026-11-11T00:30:00.000Z')
    expect(formatClock(65)).toBe('01:05')
    expect(formatClock(3725)).toBe('1:02:05')
    expect(formatClock(-3)).toBe('00:00')
  })
})

describe('test arena', () => {
  it('lists tests and starts one', async () => {
    const user = userEvent.setup()
    const calls = mockApi({
      'GET /tests': [TEST], 'GET /tests/attempts': [],
      'POST /tests/t1/start': { attempt_id: 'att1' },
      'GET /tests/attempts/att1': attempt(), 'GET /tests/attempts/att1/questions': QUESTIONS,
    })
    renderAt('/tests')
    expect(await screen.findByRole('heading', { name: 'Practice Test 1' })).toBeInTheDocument()
    expect(screen.getByText(/negative marking/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /start test/i }))
    expect(await screen.findByText('What is 15% of 240?')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST' && c.url === '/tests/t1/start')).toBe(true)
  })

  it('offers to resume an in-progress attempt instead of starting another', async () => {
    mockApi({ 'GET /tests': [TEST], 'GET /tests/attempts': [attempt()] })
    renderAt('/tests')
    const card = (await screen.findByRole('heading', { name: 'Practice Test 1' })).closest('article')!
    expect(within(card).getByRole('link', { name: /resume/i })).toHaveAttribute('href', '/tests/attempts/att1')
    expect(within(card).queryByRole('button', { name: /start test/i })).toBeNull()
  })

  it('saves answers as JSON, tracks the palette, and submits after confirmation', async () => {
    const user = userEvent.setup()
    const calls = mockApi({
      'GET /tests/attempts/att1': attempt(), 'GET /tests/attempts/att1/questions': QUESTIONS,
      'PUT /tests/attempts/att1/answers': { message: 'Answer saved' },
      'POST /tests/attempts/att1/submit': { attempt_id: 'att1', score_obtained: 1.5, max_score: 4, correct: 1, incorrect: 1, unanswered: 0, accuracy: 50, status: 'completed' },
      'GET /tests/attempts': [],
    })
    renderAt('/tests/attempts/att1')
    expect(await screen.findByText('What is 15% of 240?')).toBeInTheDocument()
    expect(screen.getByRole('timer')).toHaveTextContent('10:00')
    // no answer key is ever rendered while the test is open
    expect(document.body.textContent).not.toMatch(/correct/i)

    await user.click(screen.getByRole('radio', { name: /thirty-six/i }))
    await waitFor(() => expect(calls.find((c) => c.method === 'PUT')?.body).toEqual({ question_id: 'q1', selected_option_key: 'b' }))
    expect(screen.getByRole('button', { name: /question 1: answered/i })).toBeInTheDocument()
    expect(await screen.findByText(/all answers saved/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /mark for review/i }))
    expect(screen.getByRole('button', { name: /question 1: answered, marked/i })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /^next/i }))
    expect(screen.getByText('Second question?')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /clear response/i }).closest('footer')!.querySelector('button')!) // clear is disabled when nothing chosen
    expect(calls.filter((c) => c.method === 'PUT')).toHaveLength(1)

    await user.click(screen.getByRole('button', { name: /submit test/i }))
    const dialog = await screen.findByRole('alertdialog')
    expect(dialog).toHaveTextContent(/1\s*Answered/)
    expect(dialog).toHaveTextContent(/1\s*Not answered/)
    await user.click(within(dialog).getByRole('button', { name: /submit test/i }))
    await waitFor(() => expect(calls.some((c) => c.url === '/tests/attempts/att1/submit')).toBe(true))
  })

  it('auto-submits when time runs out', async () => {
    mockApi({
      'GET /tests/attempts/att1': attempt({ seconds_remaining: 1 }), 'GET /tests/attempts/att1/questions': QUESTIONS,
      'POST /tests/attempts/att1/submit': { attempt_id: 'att1' }, 'GET /tests/attempts': [],
      'GET /tests/attempts/att1/review': REVIEW,
    })
    const calls = (fetch as unknown as { mock: { calls: unknown[][] } }).mock.calls
    renderAt('/tests/attempts/att1')
    expect(await screen.findByText('What is 15% of 240?')).toBeInTheDocument()
    await waitFor(() => expect(calls.some((c) => String(c[0]).endsWith('/submit'))).toBe(true), { timeout: 4000 })
    expect(calls.filter((c) => String(c[0]).endsWith('/submit'))).toHaveLength(1) // exactly once
  })

  it('sends a finished attempt to its result instead of the runner', async () => {
    mockApi({ 'GET /tests/attempts/att1': SUBMITTED, 'GET /tests/attempts/att1/review': REVIEW })
    renderAt('/tests/attempts/att1')
    expect(await screen.findByRole('heading', { name: /your result/i })).toBeInTheDocument()
  })

  it('shows the score, review and filters by outcome', async () => {
    const user = userEvent.setup()
    mockApi({ 'GET /tests/attempts/att1': SUBMITTED, 'GET /tests/attempts/att1/review': REVIEW })
    renderAt('/tests/attempts/att1/result')
    expect(await screen.findByText(/1\.5/)).toBeInTheDocument()
    expect(await screen.findByText('240 x 15 / 100 = 36.')).toBeInTheDocument()
    expect(screen.getAllByText(/correct answer/i).length).toBeGreaterThan(0)

    await user.click(screen.getByRole('tab', { name: /incorrect/i }))
    expect(screen.queryByText('What is 15% of 240?')).toBeNull()
    expect(screen.getByText('Second question?')).toBeInTheDocument()
    expect(screen.getByText('Your answer')).toBeInTheDocument()
  })

  it('requires sign-in', async () => {
    authStore.getState().clear()
    mockApi({})
    renderAt('/tests/attempts/att1')
    expect(await screen.findByRole('heading', { name: /good to see you again/i })).toBeInTheDocument()
  })
})
