// Service worker: precache the app shell, then serve cache-first and refresh in the background.
// Bump CACHE when you ship changes so old files are dropped.
const CACHE = 'padav-v2';
const ASSETS = [
  '/',
  '/static/index.html',
  '/static/css/styles.css',
  '/static/js/app.js',
  '/static/js/dom.js',
  '/static/js/i18n.js',
  '/static/js/pack.js',
  '/static/js/scoring.js',
  '/static/js/store.js',
  '/static/js/api.js',
  '/static/manifest.webmanifest',
  '/static/icons/icon.svg',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/icon-maskable-512.png',
  '/api/pack',
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== self.location.origin) return;
  // Never cache API traffic: responses are per-user and must not outlive the session
  // (shared devices) or be served stale after logout.
  if (url.pathname.startsWith('/api/') || req.headers.has('Authorization')) return;

  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(req, { ignoreSearch: true });
    const network = fetch(req)
      .then((res) => { if (res.ok) cache.put(req, res.clone()); return res; })
      .catch(() => null);
    if (cached) { event.waitUntil(network); return cached; }
    const fresh = await network;
    if (fresh) return fresh;
    if (req.mode === 'navigate') return (await cache.match('/static/index.html')) || Response.error();
    return Response.error();
  })());
});