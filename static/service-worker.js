const CACHE_NAME = "obra-cache-v1";
const urlsToCache = [
  "/",
  "/vistorias",
  "/comunicacoes",
  "/agendamentos",
  "/static/icon-192.png",
  "/static/icon-512.png",
  "/static/manifest.json",
  "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
];

// Instalação do Service Worker
self.addEventListener("install", event => {
  console.log("✅ Service Worker instalado");
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(urlsToCache);
    })
  );
  self.skipWaiting(); // força ativação imediata
});

// Ativação do Service Worker
self.addEventListener("activate", event => {
  console.log("✅ Service Worker ativado");
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(name => {
          if (name !== CACHE_NAME) {
            console.log("🧹 Limpando cache antigo:", name);
            return caches.delete(name);
          }
        })
      );
    })
  );
  self.clients.claim(); // assume controle imediato
});

// Interceptação de requisições
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request).catch(() => {
        // Aqui você pode retornar uma página de fallback offline se quiser
      });
    })
  );
});
