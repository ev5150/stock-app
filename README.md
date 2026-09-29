# DEBUとCHIKAのストック帳

家の在庫を夫婦で共有して、**残り1つ・欠品になった瞬間にiPhoneへ通知**するアプリです。
iPhoneのホーム画面に置いて、アプリとして使います（PWA）。

- アプリ: https://ev5150.github.io/stock-app/
- データ: Supabase（プロジェクト `stock-app`、東京リージョン、無料プラン）

```
iPhone（ホーム画面のアプリ）
   │  ＋／− を押す
   ▼
Supabase（データベース） ── 残り1以下になったら ──▶ 通知関数 ──▶ 通知オンの全員のiPhoneへ
   ▲
GitHub Pages（アプリの画面を置く場所）
```

## ファイル

| ファイル | 役割 |
|---|---|
| `index.html` | アプリの画面 |
| `config.js` | Supabase の接続先（公開して問題ない値だけ） |
| `sw.js` | オフライン表示と通知の受け取り |
| `manifest.webmanifest` / `icons/` | ホーム画面のアイコンと名前 |
| `supabase/migrations/` | データベースの定義 |
| `supabase/functions/notify-low-stock/` | 通知を送る関数 |
| `supabase/config.toml` | ログイン設定など |
| `tools/check_backend.py` | サーバー側の動作確認 |
| `tools/setup_assets.py` | アイコンを作り直すスクリプト |

GitHub に上がらないもの（`.gitignore` 済み）:
- `secrets.local.txt` … データベースのパスワード
- `tools/bin/` … Supabase CLI

通知用の鍵と合言葉は、Supabase の中で自動的に作られて `app_secrets` テーブルに保存されます（アプリからは見えません）。

## 使う人

- `members` テーブルに載っているメールアドレスの人だけが、在庫を見たり変えたりできます。
- ログインはメールアドレスとパスワードです。初回は「はじめて使う」から自分で登録します。
  - 無料プランでは、ログイン用メールの文面を変えられないため、この方式にしています。
- パスワードを忘れたら、ログイン画面の「パスワードを忘れたとき」から再設定します（メールが届きます）。

使う人を変えるとき:  Supabase ダッシュボード → Table Editor → `members` で追加・削除。

## iPhone に入れる手順

1. **Safari** で https://ev5150.github.io/stock-app/ を開く（Chrome など他のアプリでは不可）
2. 下の共有ボタン（□に↑）→「**ホーム画面に追加**」
3. ホーム画面の「ストック帳」アイコンから開く
4. 「はじめて使う」→ メールアドレスとパスワードを決めて登録
5. 右上の ⚙ →「**通知をオンにする**」→「許可」

iOS 16.4 以上が必要です（設定 → 一般 → 情報 → iOSバージョン）。

## 更新のしかた

- **画面を直したとき**: `sw.js` の `VERSION` を `v2`, `v3` … と上げてから push。iPhone 側はアプリを一度閉じて開き直すと切り替わります。
- **データベースを変えるとき**: `supabase/migrations/` に新しい SQL ファイルを追加して
  `.\tools\bin\supabase.exe db push`
- **通知関数を直したとき**:
  `.\tools\bin\supabase.exe functions deploy notify-low-stock --no-verify-jwt --use-api`
- **動作確認**: `python tools/check_backend.py`

## 注意

- **Supabase の無料プランは、7日間まったく使われないと一時停止**します。毎日使っていれば問題ありません。止まったらダッシュボードから再開できます。
- 通知は、数を減らした本人も含め、通知をオンにしている全員に届きます。
