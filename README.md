GitHub Actions トリガ

cron: "0 6 * * *" → JST 15:00 に起動

または workflow_dispatch で手動実行

ワークフロー手順

Checkout – リポジトリ取得

credentials.json 作成 – SERVICE_ACCOUNT_JSON Secret を書き出す

Chromium & Chromedriver インストール – Selenium 用

Python セットアップ – 3.12 + requirements.txt

twitter_key.json 作成 – Twitter API トークン 5 種を Secrets から書き出し

tweepybot_scraping_tuge.py 実行

Tableau User Group のイベント一覧ページを Selenium で開く

タイトル・URL・日付を取得し event_details.csv 生成

Google Sheets（URL 固定）に書き込み

tweepybot.py 実行

Google Sheets から “今日以降の未投稿イベント” を取得

日付やタグを整形してツイート本文を生成

Tweepy v2 で X(Twitter) へ投稿

投稿済み行に “posted” フラグを書き戻し

ジョブ終了 – 正常なら exit 0、失敗時はログに残る

エラーハンドリング

認証失敗 → Google / Twitter いずれも RefreshError や 4xx が出力

シート側で重複フラグが無い場合のみツイートするロジックで多重投稿を防止

監視・保守

CI 成功／失敗は GitHub の workflow run で確認

Google Sheets 側で “posted” 列を手動修正すれば再投稿も可能
