# Tweepy Bot Multi-Client

このリポジトリは、**複数クライアント**向けにGoogle SheetsのデータをTwitterへ投稿するBotを、GitHub Actionsで**完全自動化**する構成を提供します。

## 目次
1. [リポジトリ構成](#リポジトリ構成)
2. [前提条件](#前提条件)
3. [セットアップ方法](#セットアップ方法)
4. [新しいボット（クライアント）を追加する手順](#新しいボットクライアントを追加する手順)
5. [運用・メンテナンス](#運用メンテナンス)

---

## リポジトリ構成

```
.github/
  workflows/    ← GitHub Actions ワークフロー定義
credentials.json (生成済み/CIで作成)
plugin_loader.py ← プラグインローダー
tweepybot.py     ← 投稿エントリポイント
plugins/         ← 各クライアントのスクレイパー集
  cl0001.py
  ...
requirements.txt
```  

---

## 前提条件

- GitHubリポジトリ（`main` ブランチ）にアクセスできること
- Google Service Account のJSONを `SERVICE_ACCOUNT_JSON` シークレットに登録済み
- 各クライアントの Twitter API キー・トークンをSecretに登録できること
- Python 3.12 + Selenium / gspread / tweepy などが動作すること

---

## セットアップ方法

1. リポジトリをクローン／フォーク
   ```bash
   git clone git@github.com:<あなたのアカウント>/tweepybot.git
   ```
2. `requirements.txt` に記載のライブラリをローカルでテストインストール
   ```bash
   pip install -r requirements.txt
   ```
3. GitHub Actions の **Settings → Secrets and variables → Actions** で下記シークレットを登録
   - `SERVICE_ACCOUNT_JSON`  (Google Service Account JSON を Base64 などで格納)
   - 各クライアント用に後述の `CLIENTXXXX_*` を登録
4. `.github/workflows/bot.yml` の `matrix.client` に最初の `cl0001` があることを確認

---

## 新しいボット（クライアント）を追加する手順

1. **プラグイン作成**  
   - `plugins/` フォルダ内に `clXXXX.py` を新規作成  
   - `def scrape():` 関数で必要なスクレイピング／データ取得を実装し、
     ```python
     return [
       {"URL": url, "完了": 0, "コメントjp": title, ...},
       ...
     ]
     ```  
   - 既存の `cl0001.py` を参考にコーディング

2. **ワークフロー定義に追加**  
   - `.github/workflows/bot.yml` 内の `strategy.matrix.client: [cl0001, ...]` に `clXXXX` を追記

3. **GitHub Secrets を登録**  
   - リポジトリの **Settings → Secrets and variables → Actions** で下記を登録
     - `CLIENTXXXX_SHEET_URL`   : 対象Google Sheets の URL
     - `CLIENTXXXX_EVENT_URLS`  : （オプション）スクレイピング対象ページの URL 一覧
     - `CLIENTXXXX_TW_BEARER_TOKEN`
     - `CLIENTXXXX_TW_CONSUMER_KEY`
     - `CLIENTXXXX_TW_CONSUMER_SECRET`
     - `CLIENTXXXX_TW_ACCESS_TOKEN`
     - `CLIENTXXXX_TW_ACCESS_SECRET`

4. **コミット & プッシュ**  
   ```bash
   git add plugins/clXXXX.py .github/workflows/bot.yml
   git commit -m "Add new client clXXXX"
   git push origin main
   ```

5. **動作確認**  
   - GitHub の **Actions → Tweepy Bot Multi-Client → Run workflow** から対象ブランチ `main` を選び、`Run workflow` ボタンをClick
   - ログを確認し、スクレイピング → Sheets 追加 → Tweet までエラーなく通ることを確認

---

## 運用・メンテナンス

- **スケジュール変更**  : `.github/workflows/bot.yml` の `on.schedule.cron` を編集
- **ロギング**          : `tweetbot.log` を確認（GitHub Actions のアーティファクト設定も可）
- **トラブル時**        : `raise` されない例外は `tweetbot.log` / `Actions` ログで確認

---

以上の手順をREADMEに記入することで、新たなクライアントボットの追加作業を**一目でわかる**状態にします。
