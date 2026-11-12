import { authStore } from '../store/auth'

const API_ROOT = '/api/v1'
let refreshPromise: Promise<boolean> | null = null

export type TokenResponse = { access_token: string; refresh_token: string; token_type: string }
export type User = {
  id: string; email: string; full_name: string | null; avatar_url: string | null
  is_active: boolean; is_verified: boolean; language: string; theme: string; created_at: string
}
export type Exam = {
  id: string; name: string; name_hi: string | null; code: string; category: string
  description: string | null; description_hi: string | null; is_active: boolean; created_at: string
}
export type Course = {
  id: string; subject_id: string; title: string; title_hi: string | null; description: string | null
  instructor: string | null; level: string; total_lessons: number; estimated_hours: number | null
  thumbnail_url: string | null; is_free: boolean; is_active: boolean; created_at: string
}
export type Overview = {
  total_tests_taken: number; average_score: number; overall_accuracy: number
  total_study_hours: number; current_streak: number; total_questions_attempted: number
  active_dates: string[]
}
export type TrendPoint = { date: string; score: number; accuracy: number; questions_attempted: number }
export type Profile = {
  id: string; user_id: string; phone: string | null; date_of_birth: string | null
  education_level: string | null; target_exams: string | null; study_goal_hours_per_week: number | null
}
export type ProfileUpdate = Partial<Pick<Profile, 'phone' | 'date_of_birth' | 'education_level' | 'study_goal_hours_per_week'>>
export type PlannerBlock = {
  id: string; title: string; subject: string | null; study_date: string
  start_time: string; end_time: string; completed: boolean; created_at: string
}

export type TestInfo = {
  id: string; exam_id: string; title: string; title_hi: string | null
  description: string | null; description_hi: string | null
  total_questions: number; duration_minutes: number; total_marks: number
  passing_marks: number; negative_marks_per_question: number; is_free: boolean
}
export type QuestionOption = { id: string; key: string; text: string; text_hi: string | null }
export type Question = {
  id: string; subject_id: string; text: string; text_hi: string | null; difficulty: string
  marks: number; negative_marks: number; options: QuestionOption[]
}
export type AttemptSummary = {
  id: string; test_id: string; test_title: string; status: string
  started_at: string; completed_at: string | null; total_questions: number
  attempted_questions: number; correct_answers: number; incorrect_answers: number
  unanswered_questions: number; score_obtained: number; max_score: number
  accuracy: number; is_submitted: boolean
}
export type AttemptAnswer = { question_id: string; selected_option_key: string | null; is_correct: boolean | null; marks_obtained: number | null }
export type AttemptDetail = AttemptSummary & { duration_minutes: number; seconds_remaining: number | null; answers: AttemptAnswer[] }
export type SubmitResult = {
  attempt_id: string; score_obtained: number; max_score: number; correct: number
  incorrect: number; unanswered: number; accuracy: number; status: string
}
export type ReviewItem = {
  question: Question; correct_option_key: string; selected_option_key: string | null
  explanation: string | null; explanation_hi: string | null
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const makeRequest = (token: string | null) => {
    const headers = new Headers(init.headers)
    if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
    if (token) headers.set('Authorization', `Bearer ${token}`)
    return fetch(`${API_ROOT}${path}`, { ...init, headers })
  }
  let response = await makeRequest(authStore.getState().accessToken)
  if (response.status === 401 && authStore.getState().refreshToken && !['/auth/login', '/auth/register', '/auth/refresh'].includes(path)) {
    if (!refreshPromise) {
      refreshPromise = (async () => {
        const refreshToken = authStore.getState().refreshToken
        if (!refreshToken) return false
        try {
          const refreshed = await fetch(`${API_ROOT}/auth/refresh`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          })
          if (!refreshed.ok) return false
          const tokens = await refreshed.json() as TokenResponse
          authStore.getState().setTokens(tokens.access_token, tokens.refresh_token)
          return true
        } catch { return false }
      })().finally(() => { refreshPromise = null })
    }
    if (await refreshPromise) response = await makeRequest(authStore.getState().accessToken)
    else authStore.getState().clear()
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null
    throw new ApiError(body?.detail || `Request failed (${response.status})`, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) { super(message); this.status = status }
}

export type PiaRun = {
  domain: string; label: string; description: string; sequence: number
  status: 'pending' | 'in_progress' | 'completed' | 'timed_out'
  question_count: number; time_limit_seconds: number; seconds_remaining: number | null
}
export type PiaSession = {
  id: string; status: 'in_progress' | 'completed'; language: string; created_at: string; completed_at: string | null
  total_questions: number; total_minutes: number; runs: PiaRun[]
}
export type PiaItem = {
  item_code: string; position: number; stem: string; options: { key: string; text: string }[]
  stimulus_type: string; asset_id: string | null; selected_key: string | null
}
export type PiaDomainScore = {
  domain: string; label: string; questions: number; correct: number; omitted: number; accuracy: number
  median_response_ms: number | null; timed_out: boolean; interrupted: boolean
}
export type PiaReport = {
  session_id: string; status: 'experimental'; form_code: string; form_version: number
  scoring_model_version: string; norm_version: string | null; total_questions: number; total_correct: number
  total_omitted: number; raw_accuracy: number; domains: PiaDomainScore[]; notices: string[]; created_at: string
}

export const api = {
  exams: () => request<Exam[]>('/exams'),
  courses: () => request<Course[]>('/courses'),
  // tz_offset lets the server count streak days in the learner's own timezone
  overview: () => request<Overview>(`/analytics/overview?tz_offset=${-new Date().getTimezoneOffset()}`),
  trends: () => request<TrendPoint[]>('/analytics/trends'),
  profile: () => request<Profile>('/users/me/profile'),
  updateProfile: (body: ProfileUpdate) => request<Profile>('/users/me/profile', { method: 'PUT', body: JSON.stringify(body) }),
  updateMe: (body: { full_name?: string; language?: 'en' | 'hi'; theme?: 'dark' | 'light' }) =>
    request<User>('/users/me', { method: 'PUT', body: JSON.stringify(body) }),
  changePassword: (current_password: string, new_password: string) =>
    request<TokenResponse>('/auth/change-password', { method: 'POST', body: JSON.stringify({ current_password, new_password }) }),
  planner: (start: string, end: string) => request<PlannerBlock[]>(`/planner?start_date=${start}&end_date=${end}`),
  addPlannerBlock: (body: Pick<PlannerBlock, 'title' | 'subject' | 'study_date' | 'start_time' | 'end_time'>) =>
    request<PlannerBlock>('/planner', { method: 'POST', body: JSON.stringify(body) }),
  completePlannerBlock: (id: string, completed: boolean) =>
    request<PlannerBlock>(`/planner/${id}`, { method: 'PATCH', body: JSON.stringify({ completed }) }),
  deletePlannerBlock: (id: string) => request<void>(`/planner/${id}`, { method: 'DELETE' }),
  tests: () => request<TestInfo[]>('/tests'),
  startTest: (testId: string) => request<{ attempt_id: string }>(`/tests/${testId}/start`, { method: 'POST' }),
  attempts: () => request<AttemptSummary[]>('/tests/attempts'),
  attempt: (id: string) => request<AttemptDetail>(`/tests/attempts/${id}`),
  attemptQuestions: (id: string) => request<Question[]>(`/tests/attempts/${id}/questions`),
  saveAnswer: (id: string, question_id: string, selected_option_key: string | null) =>
    request<{ message: string }>(`/tests/attempts/${id}/answers`, { method: 'PUT', body: JSON.stringify({ question_id, selected_option_key }) }),
  submitAttempt: (id: string) => request<SubmitResult>(`/tests/attempts/${id}/submit`, { method: 'POST' }),
  attemptReview: (id: string) => request<ReviewItem[]>(`/tests/attempts/${id}/review`),
  register: (body: { email: string; password: string; full_name: string }) =>
    request<TokenResponse>('/auth/register', { method: 'POST', body: JSON.stringify(body) }),
  login: (body: { email: string; password: string }) =>
    request<TokenResponse>('/auth/login', { method: 'POST', body: JSON.stringify(body) }),
  me: () => request<User>('/users/me'),
  myExams: () => request<{ id: string; exam_id: string; is_primary: boolean }[]>('/users/me/exams'),
  addExam: (exam_id: string, is_primary: boolean) =>
    request('/users/me/exams', { method: 'POST', body: JSON.stringify({ exam_id, is_primary }) }),
  removeExam: (exam_id: string) =>
    request(`/users/me/exams/${exam_id}`, { method: 'DELETE' }),
  piaConsent: (age: number, guardian_consent: boolean) =>
    request<{ id: string }>('/pia/consent', { method: 'POST', body: JSON.stringify({ accepted: true, age, guardian_consent }) }),
  piaStart: (language: 'en' | 'hi') => request<PiaSession>('/pia/sessions', { method: 'POST', body: JSON.stringify({ language }) }),
  piaSession: (id: string) => request<PiaSession>(`/pia/sessions/${id}`),
  piaStartSubtest: (id: string, domain: string) => request<PiaItem[]>(`/pia/sessions/${id}/subtests/${domain}/start`, { method: 'POST' }),
  piaItems: (id: string, domain: string) => request<PiaItem[]>(`/pia/sessions/${id}/subtests/${domain}/items`),
  piaAnswer: (id: string, domain: string, item_code: string, selected_key: string | null, client_response_ms?: number) =>
    request<{ saved: boolean; seconds_remaining: number }>(`/pia/sessions/${id}/subtests/${domain}/answers`, {
      method: 'PUT', body: JSON.stringify({ item_code, selected_key, client_response_ms }),
    }),
  piaEvent: (id: string, domain: string, event_type: 'interruption' | 'resume', payload?: Record<string, string>) =>
    request<void>(`/pia/sessions/${id}/subtests/${domain}/events`, { method: 'POST', body: JSON.stringify({ event_type, payload }) }),
  piaComplete: (id: string, domain: string) => request<PiaSession>(`/pia/sessions/${id}/subtests/${domain}/complete`, { method: 'POST' }),
  piaFinish: (id: string) => request<PiaReport>(`/pia/sessions/${id}/finish`, { method: 'POST' }),
  piaReport: (id: string) => request<PiaReport>(`/pia/sessions/${id}/report`),
  logout: (refresh_token: string) =>
    request<{ message: string }>('/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token }) }),
}
