#!/usr/bin/env python
# coding: utf-8

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import tweepy
import datetime
import json
import logging
import sys
import traceback

# ── ロギング設定 ─────────────────────────
logging.basicConfig(
    filename='tweetbot.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info("Logging configured")

# ── Google Sheets 認証準備 ────────────────────
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    'credentials.json', scope
)
client = gspread.authorize(creds)

SPREADSHEET_URL = (
    'https://docs.google.com/spreadsheets/d/'
    '1RAZwuhJkpkca4QaVLVO9fzW68TKqLTxIhSfhrGR1Jjw/edit?usp=sharing'
)

try:
    spreadsheet = client.open_by_url(SPREADSHEET_URL)
    sheet = spreadsheet.sheet1
except Exception as e:
    logging.error(f"Unable to open spreadsheet: {e}")
    sheet = None

# ── Twitter 認証 ─────────────────────────────
def load_twitter_keys(path='twitter_key.json'):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

k = load_twitter_keys()
twitter_client = tweepy.Client(
    bearer_token=k['BEARER_TOKEN'],
    consumer_key=k['CONSUMER_KEY'],
    consumer_secret=k['CONSUMER_SECRET'],
    access_token=k['ACCESS_TOKEN'],
    access_token_secret=k['ACCESS_SECRET']
)

# ── ツイート用ユーティリティ ───────────────────
def tweet(text: str):
    try:
        resp = twitter_client.create_tweet(text=text)
        tweet_id = resp.data['id']
        logging.info(f"Tweeted: {text} (id={tweet_id})")
        return tweet_id
    except Exception as e:
        logging.error(f"Tweet failed: {e}")
        return None

# ── イベント取得関数（空文字チェック対応版） ─────────
def get_pending(sheet, today_str, weekday, ampm):
    if sheet is None:
        return []

    try:
        records = sheet.get_all_records()
    except Exception as e:
        logging.error(f"Sheet fetch error: {e}")
        return []

    # 完了フラグが 0 の行だけ返す
    return [ row for row in records if row.get('完了') != 1 ]

# ── 投稿後の完了フラグ更新 ───────────────────
def mark_as_done(sheet, urls):
    if sheet is None or not urls:
        return
    try:
        for url in urls:
            cell = sheet.find(url)
            if cell:
                # URL の右隣（完了列）に 1 を書き込む
                sheet.update_cell(cell.row, cell.col + 1, 1)
    except Exception as e:
        logging.error(f"Update sheet error: {e}")

# ── メイン処理 ─────────────────────────────
def main():
    today = datetime.datetime.today()
    today_str = today.strftime('%Y/%m/%d')
    weekday = today.weekday()
    ampm = 0 if today.hour < 12 else 1

    pending = get_pending(sheet, today_str, weekday, ampm)

    # 取得レコードがゼロ → 失敗として通知
    if not pending:
        logging.warning("No info fetched; sending failure tweet.")
        tweet("Failed to get information")
        return

    tweeted = []
    for row in pending:
        url = row.get('URL', '').strip()
        comment = row.get('コメントjp', '').strip()
        text = f"{comment} {url}".strip()
        if text and tweet(text):
            tweeted.append(url)

    mark_as_done(sheet, tweeted)

# ── エントリポイント ─────────────────────────
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        traceback.print_exc()
        tweet("Failed to get information")
        sys.exit(1)
