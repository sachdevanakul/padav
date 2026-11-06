/**
 * API client for the Padav FastAPI backend.
 * Replaces the old IndexedDB/localStorage store with REST calls.
 */

const API_BASE = "/api";

async function _json(res) {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${text}`);
  }
  return res.json();
}

/** Fetch the full question pack (subjects, quizzes, questions). */
export async function fetchPack() {
  const res = await fetch(`${API_BASE}/pack`);
  return _json(res);
}

/** Fetch a single quiz with its questions. */
export async function fetchQuiz(quizId) {
  const res = await fetch(`${API_BASE}/quizzes/${quizId}`);
  return _json(res);
}

/** Save a completed quiz attempt. Server computes the score. */
export async function saveAttempt(attempt) {
  const res = await fetch(`${API_BASE}/attempts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(attempt),
  });
  return _json(res);
}

/** List all attempts, newest first. */
export async function listAttempts() {
  const res = await fetch(`${API_BASE}/attempts`);
  return _json(res);
}

/** Get a single attempt by ID. */
export async function getAttempt(id) {
  const res = await fetch(`${API_BASE}/attempts/${id}`);
  return _json(res);
}

/** Mark an attempt as synced. */
export async function markSynced(id) {
  const res = await fetch(`${API_BASE}/attempts/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ synced: true }),
  });
  return _json(res);
}

/** Compute score for a set of answers without saving. */
export async function computeScore(marksPerQuestion, negativeMarks, answers) {
  const res = await fetch(`${API_BASE}/score`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ marks_per_question: marksPerQuestion, negative_marks: negativeMarks, answers }),
  });
  return _json(res);
}

/** Get translated strings for a language. */
export async function fetchLangStrings(lang) {
  const res = await fetch(`${API_BASE}/lang/${lang}`);
  return _json(res);
}

/** List available languages. */
export async function fetchLanguages() {
  const res = await fetch(`${API_BASE}/languages`);
  return _json(res);
}