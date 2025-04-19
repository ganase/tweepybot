# Tweepy Bot – Auto‑tweet & Google Sheets Sync

Tweepy Bot は **X (Twitter) API v2** と **Google Sheets** を連携し、  
指定サイトをスクレイピングして得たイベント情報をツイートする CI ボットです。  
GitHub Actions で毎日自動実行され、失敗時は “Failed to get information” を投稿します。

---

## Quick Start (5 minutes)

1. **Fork / Clone**
   ```bash
   gh repo fork ganase/tweepybot --clone
   cd tweepybot
   ```

2. **Secrets を登録（Settings → Secrets → Actions）**

   | Name | Value |
   |------|-------|
   | `SERVICE_ACCOUNT_JSON` | Google Cloud で発行したサービスアカウント JSON |
   | `TW_BEARER_TOKEN` | X API Bearer Token |
   | `TW_CONSUMER_KEY` / `TW_CONSUMER_SECRET` | X API Key / Secret |
   | `TW_ACCESS_TOKEN`  / `TW_ACCESS_SECRET` | X Access Token / Secret |

3. **シート URL を修正**  
   `tweepybot.py` → `SPREADSHEET_URL` を自分の Google Sheets に変更  
   （列構成サンプルは docs/DEVELOPER_GUIDE.md を参照）

4. **手動テスト**  
   GitHub → **Actions** → “Tweepy Bot Workflow” → **Run workflow**  
   成功すると X アカウントにツイートが投稿されます。

---

## スケジュール

| Cron 設定 | 実行時刻 |
|-----------|-----------|
| `0 6 * * *` | **UTC 06:00 → JST 15:00** 毎日 |

変更したい場合は `.github/workflows/bot.yml` の `cron` を編集してください。

---

## カスタマイズ

スクレイピング対象が変わる場合、  
**`tweepybot_scraping_tuge.py` を全面書き換え** する必要があります。  
詳しい手順は [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) を参照してください。

---

## License

MIT © 2025  
