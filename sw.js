// Capitales del Mundo: guarda la página para usarla sin conexión.
// La versión cambia con cada armado, así que una versión nueva sustituye a la vieja.
const CACHE = "capitales-90352a874f";
const BASE = ["./", "index.html", "manifest.webmanifest", "icono-192.png", "icono-512.png"];
self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(BASE); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
self.addEventListener("fetch", function (e) {
  if (e.request.method !== "GET") return;
  const esPagina = e.request.mode === "navigate";
  e.respondWith(
    // la página: primero la red, para ver datos nuevos; sin red, la copia
    // fotos y tipografías: primero la copia, y se guardan al verlas por primera vez
    (esPagina ? fetch(e.request).then(guarda(e.request)).catch(function () { return caches.match(e.request).then(function (r) { return r || caches.match("index.html"); }); })
      : caches.match(e.request).then(function (r) { return r || fetch(e.request).then(guarda(e.request)); }))
  );
});
function guarda(peticion) {
  return function (resp) {
    if (resp && (resp.ok || resp.type === "opaque")) {
      const copia = resp.clone();
      caches.open(CACHE).then(function (c) { c.put(peticion, copia); });
    }
    return resp;
  };
}
