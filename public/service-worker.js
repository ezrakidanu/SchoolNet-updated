/* Cache only public, versioned app-shell assets. Never cache rendered pages or user data. */
const CACHE_NAME = 'schoolnet-shell-v3';
const SHELL_ASSETS = [
  '/manifest.webmanifest',
  '/static/css/styles.css',
  '/static/js/app.js',
  '/static/js/icons.js',
  '/static/images/logo.svg',
  '/static/images/science-lab.jpg',
  '/static/images/pwa-180.png',
  '/static/images/pwa-192.png',
  '/static/images/pwa-512.png',
  '/static/images/pwa-maskable-512.png',
];

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await Promise.all(SHELL_ASSETS.map(async path => {
      try {
        const response = await fetch(path, { cache: 'reload' });
        if (response.ok && response.type === 'basic') await cache.put(path, response);
      } catch (_) {
        // A missed asset can be retrieved after the device reconnects.
      }
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith('schoolnet-') && key !== CACHE_NAME)
      .map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Navigation and application endpoints always go to the network. In particular,
  // feed pages are dynamic and must not be replayed as an offline cached account view.
  if (request.mode === 'navigate' || url.pathname.startsWith('/auth/')
      || url.pathname.startsWith('/api/') || url.pathname.startsWith('/posts/')) return;

  const cacheable = SHELL_ASSETS.includes(url.pathname);
  if (!cacheable) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    try {
      const response = await fetch(request);
      if (response.ok && response.type === 'basic') {
        try { await cache.put(request, response.clone()); } catch (_) { /* Return the network response. */ }
      }
      return response;
    } catch (_) {
      return (await cache.match(request)) || Response.error();
    }
  })());
});
