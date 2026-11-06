/**
 * Local persistence. Attempts live in IndexedDB (with each attempt's answers embedded, so a save is
 * atomic). If IndexedDB is unavailable (some private modes) we fall back to memory for the session.
 * Attempt ids are UUIDs so a future sync can upload them idempotently.
 */
const DB_NAME = 'padav';
const STORE = 'attempts';
const memory = [];
let dbPromise = null;

function open() {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') return reject(new Error('IndexedDB unavailable'));
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      const s = req.result.createObjectStore(STORE, { keyPath: 'id' });
      s.createIndex('completedAt', 'completedAt');
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return dbPromise;
}

const wrap = (request) => new Promise((resolve, reject) => {
  request.onsuccess = () => resolve(request.result);
  request.onerror = () => reject(request.error);
});

export function uuid() {
  if (globalThis.crypto?.randomUUID) return crypto.randomUUID();
  return 'id-' + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
}

export async function saveAttempt(attempt) {
  try {
    const db = await open();
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).put(attempt);
    await new Promise((resolve, reject) => {
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  } catch {
    memory.push(attempt);
  }
}

/** Newest first. */
export async function listAttempts() {
  let stored = [];
  try {
    const db = await open();
    stored = await wrap(db.transaction(STORE).objectStore(STORE).getAll());
  } catch { /* fall through to memory */ }
  return [...stored, ...memory].sort((a, b) => b.completedAt - a.completedAt);
}

export async function getAttempt(id) {
  try {
    const db = await open();
    const found = await wrap(db.transaction(STORE).objectStore(STORE).get(id));
    if (found) return found;
  } catch { /* fall through */ }
  return memory.find((a) => a.id === id) ?? null;
}
