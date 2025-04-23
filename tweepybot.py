#!/usr/bin/env python
# coding: utf-8

import os
import logging
import sys
import traceback
import json
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import tweepy

# ── ロギング設定 ─────────────────────────
logging.basicConfig(
    filename='tweetbot.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info("Logging configured")

# ── Google Sheets 認証 ────────────────────
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# 環境変数からシート URL と GID を取得
SPREADSHEET_URL = os.environ.get("SPREADSHEET_URL", "")
TARGET_GID      = int(os.environ.get("GID", "803084007"))

# シートタブを取得（gid 優先、なければ先頭シート）
spreadsheet = client.open_by_url(SPREADSHEET_URL)
sheet = None
for ws in spreadsheet.worksheets():
    if ws.id == TARGET_GID:
        sheet = ws
        break
if sheet is None:
    sheet = spreadsheet.sheet1

# ── Twitter 認証 ──────────────────────────
def load_twitter_keys(path='twitter_key.json'):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

twitter_keys = load_twitter_keys()
twitter_client = tweepy.Client(
    bearer_token=twitter_keys['BEARER_TOKEN'],
    consumer_key=twitter_keys['CONSUMER_KEY'],
    consumer_secret=twitter_keys['CONSUMER_SECRET'],
    access_token=twitter_keys['ACCESS_TOKEN'],
    access_token_secret=twitter_keys['ACCESS_SECRET']
)

# ── 未完了URL取得 ──────────────────────────
def get_pending_urls(sheet):
    """
    完了フラグが0の行をすべて返す
    """
    try:
        records = sheet.get_all_records()
        return [row for row in records if row.get('完了') != 1]
    except Exception as e:
        logging.error(f"Error loading pending URLs: {e}")
        return []

# ── ツイートユーティリティ ────────────────────
def tweet_url(url, comment):
    text = f"{comment} {url}".strip()
    try:
        resp = twitter_client.create_tweet(text=text)
        tweet_id = resp.data['id']
        logging.info(f"Tweeted: {text} (id={tweet_id})")
        return tweet_id
    except Exception as e:
        logging.error(f"Tweet failed: {text}: {e}")
        return None

# ── 完了フラグ更新 ─────────────────────────
def mark_as_done(sheet, urls):
    try:
        for u in urls:
            cell = sheet.find(u)
            if cell:
                sheet.update_cell(cell.row, cell.col + 1, 1)
    except Exception as e:
        logging.error(f"Error updating sheet: {e}")

# ── メイン処理 ─────────────────────────────
def main():
    pending_urls = get_pending_urls(sheet)
    logging.info(f"Pending URLs: {pending_urls}")

    # 対象なし → フォールバックツイート
    if not pending_urls:
        logging.info("No pending URLs; sending fallback tweet.")
        tweet_url(
            "https://usergroups.tableau.com/events/#/list",
            "本日はお知らせはないドン！次のサイトをチェックドン！"
        )
        return

    tweeted = []
    for row in pending_urls:
        url     = row.get('URL', '').strip()
        comment = row.get('コメントjp', row.get('コメント', '')).strip()
        if url and tweet_url(url, comment):
            tweeted.append(url)

    if tweeted:
        mark_as_done(sheet, tweeted)
        logging.info(f"Marked as done: {tweeted}")

# ── エントリポイント ─────────────────────────
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        traceback.print_exc()
        tweet_url(
            "https://usergroups.tableau.com/events/#/list",
            "本日はお知らせはないドン！次のサイトをチェックドン！"
        )
        sys.exit(1)
