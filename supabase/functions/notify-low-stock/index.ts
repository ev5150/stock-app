// 在庫が残り1・欠品になったとき、登録されている全スマホに通知を送る。
//   POST … DB のトリガー（schema.sql の notify_low_stock）から呼ばれ、通知を送る
//   GET  … アプリが通知を登録するときに、公開鍵を取りに来る
// 通知用の鍵（VAPID）は初回に自動で作り、app_secrets テーブルに保存する。
// なので、ダッシュボードで秘密の値を設定する必要はない。
import webpush from "npm:web-push@3.6.7";
import { createClient } from "npm:@supabase/supabase-js@2";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "content-type",
};

const b64url = (buf: ArrayBuffer) =>
  btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

async function getSecret(key: string): Promise<string | undefined> {
  const { data, error } = await supabase.from("app_secrets").select("value").eq("key", key).maybeSingle();
  if (error) throw error;
  return data?.value;
}

let vapid: { publicKey: string; privateKey: string } | null = null;

async function loadVapid() {
  if (vapid) return vapid;
  let publicKey = await getSecret("vapid_public");
  let privateKey = await getSecret("vapid_private");
  if (!publicKey || !privateKey) {
    const pair = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
    const pub = b64url(await crypto.subtle.exportKey("raw", pair.publicKey));
    const jwk = await crypto.subtle.exportKey("jwk", pair.privateKey);
    // 同時に 2 回呼ばれても、先に保存された方を使う
    await supabase.from("app_secrets").upsert(
      [{ key: "vapid_public", value: pub }, { key: "vapid_private", value: jwk.d! }],
      { onConflict: "key", ignoreDuplicates: true },
    );
    publicKey = await getSecret("vapid_public");
    privateKey = await getSecret("vapid_private");
  }
  const { data: member } = await supabase.from("members").select("email").limit(1).maybeSingle();
  webpush.setVapidDetails(`mailto:${member?.email ?? "admin@example.com"}`, publicKey!, privateKey!);
  vapid = { publicKey: publicKey!, privateKey: privateKey! };
  return vapid;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });

  if (req.method === "GET") {
    const { publicKey } = await loadVapid();
    return Response.json({ publicKey }, { headers: CORS });
  }

  const secret = await getSecret("webhook_secret");
  if (!secret || req.headers.get("x-webhook-secret") !== secret) {
    return new Response("forbidden", { status: 403 });
  }
  await loadVapid();

  const { name, qty } = await req.json();
  const payload = JSON.stringify({
    title: qty <= 0 ? "欠品しました" : "残りわずかです",
    body: qty <= 0 ? `${name}：欠品。買うものに追加しました` : `${name}：残り${qty}。買うものに追加しました`,
    tag: `stock-${name}`,
  });

  const { data: subs, error } = await supabase
    .from("push_subscriptions")
    .select("endpoint, p256dh, auth");
  if (error) return new Response(error.message, { status: 500 });

  let sent = 0;
  await Promise.all((subs ?? []).map(async (s) => {
    try {
      await webpush.sendNotification(
        { endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } },
        payload,
        { TTL: 60 * 60 * 24 },
      );
      sent++;
    } catch (e) {
      // 404/410 はアプリが削除されたなどで無効になった登録先。片付ける
      const status = (e as { statusCode?: number }).statusCode;
      if (status === 404 || status === 410) {
        await supabase.from("push_subscriptions").delete().eq("endpoint", s.endpoint);
      } else {
        console.error("push failed", status, e);
      }
    }
  }));

  return Response.json({ sent });
});
