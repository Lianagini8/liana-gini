// Minimal service worker: caches the app shell (HTML/JS, not media) so the
// installed icon opens instantly and the shell survives brief offline gaps.
// Does not cache videos/photos — those stay network-only.
const CACHE = 'liana-gini-shell-v4';
const SHELL = [
  'mobile.html',
  'assets/js/dc-runtime.js',
  'assets/js/image-slot.js',
  'assets/media/hero-poster.jpg',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/')) return; // payments and downloads: always network
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).catch(() => cached);
    })
  );
});
