"""サーバー側の動作確認スクリプト（在庫データは最後に元に戻す）。

使い方:  python tools/check_backend.py   （psycopg が必要: pip install "psycopg[binary]"）
- 権限: members に載っていない人には品目が見えないこと
- 通知: 残り2→1 にすると、通知関数が呼ばれて 200 が返ること
"""
import json
import time
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent
ref = (ROOT / "supabase/.temp/project-ref").read_text().strip()
pw = [l.split("=", 1)[1].strip() for l in (ROOT / "secrets.local.txt").read_text(encoding="utf-8").splitlines() if l.startswith("DB_PASSWORD=")][0]
host = (ROOT / "supabase/.temp/pooler-url").read_text().strip().rsplit("@", 1)[1].split(":")[0]

with psycopg.connect(host=host, port=5432, dbname="postgres", user=f"postgres.{ref}", password=pw, autocommit=True) as c:
    cur = c.cursor()
    cur.execute("insert into public.items (name, cat, qty, alert_at) values ('動作確認用', 'その他', 2, 1) returning id")
    item_id = cur.fetchone()[0]
    try:
        # 権限の確認：ログイン中の人として見えるか
        def visible_as(email):
            cur.execute("begin")
            cur.execute("set local role authenticated")
            cur.execute("select set_config('request.jwt.claims', %s, true)", (json.dumps({"email": email, "role": "authenticated"}),))
            cur.execute("select count(*) from public.items where id = %s", (item_id,))
            n = cur.fetchone()[0]
            # 頼まれたもの：その人として登録して読めるか（最後に取り消す）
            try:
                cur.execute("insert into public.requests (name, amount, count) values ('動作確認', '1本', 1)")
                cur.execute("select count(*) from public.requests where name = '動作確認'")
                n += cur.fetchone()[0]
            except psycopg.errors.InsufficientPrivilege:
                pass
            cur.execute("rollback")
            return n

        cur.execute("select email from public.members order by email")
        members = [r[0] for r in cur.fetchall()]
        print("登録メンバー:", len(members), "人")
        print("メンバーには見える:", visible_as(members[0]) == 2)
        print("部外者には見えない:", visible_as("stranger@example.com") == 0)

        # 通知の確認：2 → 1
        cur.execute("select coalesce(max(id), 0) from net._http_response")
        before = cur.fetchone()[0]
        cur.execute("update public.items set qty = 1 where id = %s", (item_id,))
        status, body = None, None
        for _ in range(20):
            time.sleep(1)
            cur.execute("select status_code, content from net._http_response where id > %s order by id desc limit 1", (before,))
            row = cur.fetchone()
            if row:
                status, body = row
                break
        print("通知関数の応答:", status, body)
    finally:
        cur.execute("delete from public.items where id = %s", (item_id,))
        print("動作確認用の品目を削除しました")
