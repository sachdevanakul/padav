/** Loads the bundled question pack (cached by the service worker for offline use). */
export async function loadPack() {
  const res = await fetch('data/question_pack.json');
  if (!res.ok) throw new Error(`pack ${res.status}`);
  const pack = await res.json();
  pack.byId = new Map(pack.questions.map((q) => [q.id, q]));
  return pack;
}
