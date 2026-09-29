// 繧｢繝励Μ縺ｮ逕ｻ髱｢繧偵が繝輔Λ繧､繝ｳ縺ｧ繧る幕縺代ｋ繧医≧縺ｫ縺励∝惠蠎ｫ縺ｮ騾夂衍繧定｡ｨ遉ｺ縺吶ｋ縲・// 逕ｻ髱｢縺ｮ繝輔ぃ繧､繝ｫ繧貞､峨∴縺溘ｉ VERSION 繧剃ｸ翫￡繧九→縲√せ繝槭・蛛ｴ繧よ眠縺励＞迚医↓蜈･繧梧崛繧上ｋ縲・const VERSION = "v6";
const CACHE = `stock-${VERSION}`;
const SHELL = [
  "./",
  "./index.html",
  "./config.js",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/apple-touch-icon.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

// 閾ｪ蛻・・繧ｵ繧､繝医・繝輔ぃ繧､繝ｫ縺ｯ縲後∪縺壹ロ繝・ヨ縲√□繧√↑繧峨く繝｣繝・す繝･縲阪ょ惠蠎ｫ繝・・繧ｿ(Supabase)縺ｯ隗ｦ繧峨↑縺・・self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== self.location.origin) return;
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      })
      .catch(() => caches.match(e.request).then((r) => r || caches.match("./index.html"))),
  );
});

self.addEventListener("push", (e) => {
  let data = {};
  try { data = e.data ? e.data.json() : {}; } catch { data = { body: e.data && e.data.text() }; }
  e.waitUntil(
    self.registration.showNotification(data.title || "DEBU縺ｨCHIKA縺ｮ繧ｹ繝医ャ繧ｯ蟶ｳ", {
      body: data.body || "雋ｷ縺・ｂ縺ｮ縺悟｢励∴縺ｾ縺励◆",
      icon: "icons/icon-192.png",
      badge: "icons/icon-192.png",
      tag: data.tag,
      data: { url: "./?tab=shop" },
    }),
  );
});

self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const target = new URL(e.notification.data?.url || "./", self.registration.scope).href;
  e.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((wins) => {
      for (const w of wins) {
        if ("focus" in w) { w.navigate(target); return w.focus(); }
      }
      return self.clients.openWindow(target);
    }),
  );
});
