-- うちのストック帳：データベース定義
-- Supabase の SQL Editor に全部貼り付けて「Run」してください。
-- 一番下の 2 か所（使う人のメールアドレス、通知関数の URL）だけ書き換えが必要です。
-- 何度実行しても大丈夫なように書いてあります。

create extension if not exists pg_net;

-- ---------------------------------------------------------------
-- 使う人（ここに載っているメールアドレスだけがデータを見られる）
-- ---------------------------------------------------------------
create table if not exists public.members (
  email text primary key
);
alter table public.members enable row level security;
-- ポリシーなし＝アプリからは読み書きできない（ダッシュボードからのみ編集）

create or replace function public.is_member()
returns boolean
language sql stable security definer set search_path = public
as $$
  select exists (
    select 1 from public.members
    where lower(email) = lower(auth.jwt() ->> 'email')
  );
$$;

-- ---------------------------------------------------------------
-- 品目
-- ---------------------------------------------------------------
create table if not exists public.items (
  id         uuid primary key default gen_random_uuid(),
  name       text not null check (char_length(name) between 1 and 40),
  cat        text not null default 'その他',
  qty        int  not null default 0 check (qty between 0 and 999),
  alert_at   int  not null default 1 check (alert_at between 0 and 99),
  updated_at timestamptz not null default now(),
  updated_by uuid default auth.uid()
);
alter table public.items enable row level security;

drop policy if exists "members manage items" on public.items;
create policy "members manage items" on public.items
  for all to authenticated
  using (public.is_member()) with check (public.is_member());

create or replace function public.touch_item()
returns trigger language plpgsql
as $$
begin
  new.updated_at := now();
  new.updated_by := auth.uid();
  return new;
end;
$$;

drop trigger if exists items_touch on public.items;
create trigger items_touch before update on public.items
  for each row execute function public.touch_item();

-- ＋／− ボタン用。2 人が同時に押しても数がずれないよう、DB 側で足し引きする
create or replace function public.adjust_qty(item_id uuid, delta int)
returns int
language sql security invoker set search_path = public
as $$
  update public.items
     set qty = greatest(0, least(999, qty + delta))
   where id = item_id
  returning qty;
$$;

-- ---------------------------------------------------------------
-- 通知の登録先（スマホごとに 1 行）
-- ---------------------------------------------------------------
create table if not exists public.push_subscriptions (
  endpoint   text primary key,
  user_id    uuid not null default auth.uid() references auth.users on delete cascade,
  p256dh     text not null,
  auth       text not null,
  created_at timestamptz not null default now()
);
alter table public.push_subscriptions enable row level security;

drop policy if exists "own subscriptions" on public.push_subscriptions;
create policy "own subscriptions" on public.push_subscriptions
  for all to authenticated
  using (user_id = auth.uid() and public.is_member())
  with check (user_id = auth.uid() and public.is_member());

-- ---------------------------------------------------------------
-- 内部設定（通知関数の URL・合言葉・通知用の鍵）
-- 権限ポリシーなし＝アプリからは見えない。通知関数（サーバー側）だけが読む。
-- 通知用の鍵は通知関数が初回に自動で作ってここへ保存する。
-- ---------------------------------------------------------------
create table if not exists public.app_secrets (
  key   text primary key,
  value text not null
);
alter table public.app_secrets enable row level security;
revoke all on public.app_secrets from anon, authenticated;

insert into public.app_secrets (key, value)
values ('webhook_secret', replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', ''))
on conflict (key) do nothing;

-- ---------------------------------------------------------------
-- 残り1・欠品になった瞬間に通知関数を呼ぶ
-- ---------------------------------------------------------------
create or replace function public.notify_low_stock()
returns trigger
language plpgsql security definer set search_path = public
as $$
declare
  fn_url text;
  secret text;
begin
  if not (
       (new.qty <= new.alert_at and old.qty > old.alert_at)   -- 通知ラインを下回った
    or (new.qty = 0 and old.qty > 0)                           -- 欠品になった
  ) then
    return new;
  end if;

  select value into fn_url from public.app_secrets where key = 'function_url';
  select value into secret from public.app_secrets where key = 'webhook_secret';
  if fn_url is null or secret is null then
    return new;
  end if;

  perform net.http_post(
    url     := fn_url,
    headers := jsonb_build_object('Content-Type', 'application/json',
                                  'x-webhook-secret', secret),
    body    := jsonb_build_object('name', new.name, 'qty', new.qty)
  );
  return new;
end;
$$;

drop trigger if exists items_notify on public.items;
create trigger items_notify after update of qty, alert_at on public.items
  for each row execute function public.notify_low_stock();

-- ---------------------------------------------------------------
-- 他の人の変更をすぐ画面に反映する（リアルタイム）
-- ---------------------------------------------------------------
do $$
begin
  alter publication supabase_realtime add table public.items;
exception when duplicate_object then null;
end $$;

-- ===============================================================
-- ▼ ここを書き換えてください ▼
-- ===============================================================

-- 1) アプリを使う人のメールアドレス（奥さんとあなた）
insert into public.members (email) values
  ('dokukinoko.acchonburike18@docomo.ne.jp'),
  ('ev5150@mac.com')
on conflict do nothing;

-- 2) 通知関数の URL（dfzjdgnzbeqajscriusy をプロジェクトの ID に）
insert into public.app_secrets (key, value) values
  ('function_url', 'https://dfzjdgnzbeqajscriusy.supabase.co/functions/v1/notify-low-stock')
on conflict (key) do update set value = excluded.value;
