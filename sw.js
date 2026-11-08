// Service Worker for 西门看看网 (Simon Kankan Daily News)
const CACHE_NAME = 'simon-kankan-v2';

const PRECACHE_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png'
];

// Install: precache essential shell assets and activate immediately
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activate: clear older caches and claim clients immediately
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((name) => {
          if (name !== CACHE_NAME) {
            return caches.delete(name);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: Network-first for navigation/HTML (ensures readers see fresh daily news),
// with offline cache fallback. Cache-first with network fallback for static assets.
self.addEventListener('fetch', (event) => {
  const req = event.request;

  // Ignore non-GET requests and unsupported schemes (e.g. chrome-extension)
  if (req.method !== 'GET' || !req.url.startsWith('http')) {
    return;
  }

  // HTML / Navigation requests: Network-First with cache fallback
  if (req.mode === 'navigate' || req.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(req, { cache: 'no-cache' })
        .then((networkRes) => {
          if (networkRes && networkRes.status === 200) {
            const resClone = networkRes.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, resClone));
          }
          return networkRes;
        })
        .catch(async () => {
          const cachedRes = await caches.match(req);
          if (cachedRes) return cachedRes;
          return caches.match('./index.html');
        })
    );
    return;
  }

  // Static assets (icons, manifest, fonts): Cache-First with network fallback
  event.respondWith(
    caches.match(req).then((cachedRes) => {
      if (cachedRes) {
        return cachedRes;
      }
      return fetch(req).then((networkRes) => {
        if (networkRes && networkRes.status === 200) {
          const resClone = networkRes.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, resClone));
        }
        return networkRes;
      }).catch(() => {
        // Return empty or fallback if resource fails offline
        return new Response('', { status: 408, statusText: 'Request timed out offline' });
      });
    })
  );
});
