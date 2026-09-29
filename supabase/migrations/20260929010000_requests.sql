-- 頼まれたもの（LINE で送られた買い物メモ）
create table if not exists public.requests (
  id         uuid primary key default gen_random_uuid(),
  name       text not null check (char_length(name) between 1 and 40),
  amount     text not null default '' check (char_length(amount) <= 20),  -- 表示用: "2本" "300g" など
  count      int check (count between 1 and 99),                         -- 個数で数えられるときだけ（在庫に足す数）
  done       boolean not null default false,
  added_item uuid references public.items on delete set null,            -- 買ったときに在庫を足した品目（取り消し用）
  added_qty  int,
  created_at timestamptz not null default now(),
  created_by uuid default auth.uid()
);
alter table public.requests enable row level security;

drop policy if exists "members manage requests" on public.requests;
create policy "members manage requests" on public.requests
  for all to authenticated
  using (public.is_member()) with check (public.is_member());

do $$
begin
  alter publication supabase_realtime add table public.requests;
exception when duplicate_object then null;
end $$;
