# Developer Guide – Tweepy Bot Customization

ここでは **ターゲットページを変更して新しい Bot を構築** するための  
フルセット手順を示します。  

---

## 1. リポジトリ準備

```bash
# GitHub 上で Fork → ローカルへ clone
gh repo fork ganase/tweepybot --clone
cd tweepybot
```

---

## 2. Google Cloud 設定

1. Google Cloud Console → 新規プロジェクト作成（任意）  
2. 「サービスアカウント」を作成し、Sheets & Drive API を有効化  
3. **JSON キー** を生成 & ダウンロード  

---

## 3. GitHub Secrets 登録

| Secret Name | 設定値 |
|-------------|--------|
| `SERVICE_ACCOUNT_JSON` | 手順 2 で取得した JSON 全文 |
| `TW_BEARER_TOKEN` etc.| X / Twitter API トークン 5 種 |

Secrets 名を変更する場合は、後述 YAML も合わせて編集してください。

---

## 4. Workflow (`.github/workflows/bot.yml`) 編集

- `cron` を希望時刻 (UTC 基準) に変更  
- Secrets 名を変更した場合 → `Write twitter_key.json` ステップの環境変数を修正  

例：日本時間 06:00 実行 → `cron: "0 21 * * *"`

---

## 5. スクレイピングスクリプト改修 (`tweepybot_scraping_tuge.py`)

1. **TARGET_URL** を新しいサイトに設定  
2. Selenium セレクタを新 DOM 構造に合わせて変更  
3. 取得したカラム名を `event_details.csv` に出力する際に統一  
4. 単体テスト  
   ```bash
   python tweepybot_scraping_tuge.py
   ```

---

## 6. Google Sheets 構築

1. 新しいスプレッドシートを作成  
2. 列ヘッダ例  
   | URL | コメントjp | 完了 | 日付 | 曜日 | AMPM |  
3. シート URL を `tweepybot.py` の `SPREADSHEET_URL` に貼り付け  

---

## 7. ツイートロジック改修 (`tweepybot.py`)

- `get_pending()` 内のフィルタ条件を必要に応じて変更  
- `for row in pending:` ループでツイート文生成を編集  
  例：タグ追加、日付フォーマット変更など  

---

## 8. 実行テスト

```bash
# Secrets 設定後に手動実行
gh workflow run "Tweepy Bot Workflow"
```

- ログにエラーが無いか確認  
- X アカウントでツイートを確認  

---

## 9. 不要ファイル整理

```bash
git rm event_details.csv tweetbot.log twitter_key.json *.ipynb
echo "event_details.csv" >> .gitignore
```

---

## 10. ドキュメント更新

- **README.md** の概要・Quick Start 更新  
- この `DEVELOPER_GUIDE.md` 内リンク・列構成例を最新化  

---

### FAQ

| 質問 | 回答 |
|------|------|
| スクレイピングが失敗すると？ | Bot は `"Failed to get information"` を 1 回ツイートします。 |
| 複数回ツイートを避けるには？ | Sheets に「完了フラグ」を書き戻すロジックで重複防止済みです。 |

---

Happy Hacking!  
