// Hermes 3.5 Single Tier - Deca Matrix Service Worker
const CACHE_NAME = 'hermes-35-deca-v3';
const STATIC_ASSETS = [
  '/static/style.css',
  '/static/manifest.json',
  '/static/favicon.ico'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          return caches.delete(key);
        })
      );
    })
  );
  self.clients.claim();
});

// Network-first: Always fetch fresh HTML and dynamic data from network
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Never cache HTML documents, API calls, or WebSockets
  if (
    url.pathname.startsWith('/api') || 
    url.pathname.startsWith('/ws') || 
    event.request.mode === 'navigate' ||
    event.request.destination === 'document' ||
    url.pathname === '/' ||
    url.pathname === '/mobile' ||
    url.pathname === '/compounding'
  ) {
    event.respondWith(fetch(event.request));
    return;
  }

  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
