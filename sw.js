// Watch Time — Service Worker
// Caches the app shell so it loads offline

const CACHE = 'watchtime-v1';
const SHELL = [
  './',
  './index.html',
  './manifest.json',
  'https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/hls.js/1.4.12/hls.min.js',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  // Network-first for YouTube/video URLs so they always load fresh
  const url = e.request.url;
  if (url.includes('youtube') || url.includes('.mp4') || url.includes('.m3u8') || url.includes('.webm')) {
    return; // let browser handle video requests natively
  }

  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(res => {
        // Cache successful GET responses for app shell assets
        if (res.ok && e.request.method === 'GET') {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return res;
      }).catch(() => caches.match('./index.html')); // offline fallback
    })
  );
});
