/** Loads the question pack from the FastAPI backend. */
export async function loadPack() {
  const res = await fetch('/api/pack');
  if (!res.ok) throw new Error(`pack ${res.status}`);
  const pack = await res.json();
  pack.byId = new Map(pack.questions.map((q) => [q.id, q]));
  return pack;
}