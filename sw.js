// tinytube — Service Worker v2.1
// Two separate caches:
//   SHELL  = app files (bumped each release to force update)
//   VIDEOS = user's saved offline videos (NEVER deleted on update)

const SHELL  = 'tinytube-shell-v2';
const VIDEOS = 'tinytube-v1'; // keep stable so saved videos survive updates

// Only cache local app files — external scripts load fine from CDN
const SHELL_FILES = ['./', './index.html', './manifest.json'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(SHELL)
      .then(c => c.addAll(SHELL_FILES))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(k => k !== SHELL && k !== VIDEOS) // preserve video cache!
          .map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = e.request.url;

  // Let these bypass the SW entirely — always need to be fresh or streamed
  if (
    url.includes('youtube.com') || url.includes('youtu.be') ||
    url.includes('vimeo.com') || url.includes('googleapis.com') ||
    url.includes('gist.github.com') || url.includes('api.github.com') ||
    url.includes('fonts.g') || url.includes('cdnjs.') ||
    url.includes('.m3u8') || url.includes('.ts?')
  ) return;

  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request)
        .then(res => {
          if (res.ok && e.request.method === 'GET') {
            caches.open(SHELL).then(c => c.put(e.request, res.clone()));
          }
          return res;
        })
        .catch(() => caches.match('./index.html'));
    })
  );
});
