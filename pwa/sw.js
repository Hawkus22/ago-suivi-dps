const CACHE = 'phare-v1';
const STATIC = [
  './',
  './index.html',
  './css/app.css',
  './js/config.js',
  './js/db.js',
  './js/renfort.js',
  './js/synthese.js',
  './js/app.js',
];

self.addEventListener('install', e =>
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC)).then(() => self.skipWaiting()))
);

self.addEventListener('activate', e =>
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  )
);

self.addEventListener('fetch', e => {
  const url = e.request.url;
  // Always network for Supabase API and CDN
  if (url.includes('supabase.co') || url.includes('cdn.jsdelivr.net')) return;

  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
