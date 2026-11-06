/**
 * Persistence layer backed by the FastAPI backend (replaces IndexedDB).
 * Attempts are stored server-side; the adapter converts between the
 * frontend camelCase format and the backend snake_case format.
 */
import {
  saveAttempt as apiSaveAttempt,
  listAttempts as apiListAttempts,
  getAttempt as apiGetAttempt,
} from './api.js';

export function uuid() {
  if (globalThis.crypto?.randomUUID) return crypto.randomUUID();
  return 'id-' + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
}

function toFrontendAttempt(a) {
  return {
    id: a.id,
    quizId: a.quiz_id,
    subjectId: a.subject_id,
    title: a.title,
    startedAt: a.started_at,
    completedAt: a.completed_at_ts,
    score: a.score,
    maxScore: a.max_score,
    correct: a.correct,
    incorrect: a.incorrect,
    unanswered: a.unanswered,
    durationSeconds: a.duration_seconds,
    syncStatus: a.synced ? 'SYNCED' : 'PENDING',
    answers: (a.answers || []).map((ans) => ({
      questionId: ans.question_id,
      subjectId: null,
      topic: null,
      position: null,
      selectedKey: ans.selected_key,
      isCorrect: ans.is_correct ?? ans.selected_key === ans.correct_key,
      timeTakenSeconds: ans.time_taken_seconds,
    })),
  };
}

export async function saveAttempt(attempt) {
  const apiAttempt = {
    quiz_id: attempt.quizId,
    subject_id: attempt.subjectId,
    title: attempt.title,
    language: 'en',
    marks_per_question: attempt.marksPerQuestion ?? 1.0,
    negative_marks: attempt.negativeMarks ?? 0.0,
    started_at: attempt.startedAt,
    completed_at: attempt.completedAt,
    duration_seconds: attempt.durationSeconds,
    answers: attempt.answers.map((ans) => ({
      question_id: ans.questionId,
      selected_key: ans.selectedKey,
      correct_key: ans.correctKey,
      is_correct: ans.isCorrect,
      time_taken_seconds: ans.timeTakenSeconds,
    })),
  };
  const saved = await apiSaveAttempt(apiAttempt);
  return toFrontendAttempt(saved);
}

export async function listAttempts() {
  const attempts = await apiListAttempts();
  return attempts.map(toFrontendAttempt);
}

export async function getAttempt(id) {
  const attempt = await apiGetAttempt(id);
  return toFrontendAttempt(attempt);
}