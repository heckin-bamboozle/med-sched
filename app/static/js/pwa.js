self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open('med-tracker-v1').then((cache) => cache.addAll([
            '/',
            '/static/css/style.css',
        ])),
    );
});

self.addEventListener('fetch', (e) => {
    e.respondWith(
        caches.match(e.request).then((response) => response || fetch(e.request)),
    );
});
