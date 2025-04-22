#!/usr/bin/env python
# coding: utf-8

import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import tweepy
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

# ── Twitter 認証準備 ─────────────────────────
def load_twitter_keys(path='twitter_key.json'):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

# JSON モジュールをインポート
import json

k = load_twitter_keys('twitter_key.json')
twitter_client = tweepy.Client(
    bearer_token=k['BEARER_TOKEN'],
    consumer_key=k['CONSUMER_KEY'],
    consumer_secret=k['CONSUMER_SECRET'],
    access_token=k['ACCESS_TOKEN'],
    access_token_secret=k['ACCESS_SECRET']
)

def tweet(text: str):
    try:
        twitter_client.create_tweet(text=text)
        logging.info(f"Tweeted: {text}")
        return True
    except Exception as e:
        logging.error(f"Tweet failed: {e}")
        return False

# ── Google Sheets 認証 ─────────────────────────
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds  = ServiceAccountCredentials.from_json_keyfile_name(
    'credentials.json', scope
)
client = gspread.authorize(creds)

SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1RAZwuhJkpkca4QaVLVO9fzW68TKqLTxIhSfhrGR1Jjw/edit"
)
try:
    spreadsheet = client.open_by_url(SPREADSHEET_URL)
    sheet = spreadsheet.sheet1
except Exception as e:
    logging.error(f"Unable to open spreadsheet: {e}")
    sheet = None

# ── 未完了レコード取得 ─────────────────────────
def get_pending(sheet):
    if sheet is None:
        return []
    try:
        records = sheet.get_all_records()
    except Exception as e:
        logging.error(f"Sheet fetch error: {e}")
        return []
    return [row for row in records if row.get('完了') != 1]

# ── 完了フラグ更新 ─────────────────────────
def mark_as_done(sheet, urls):
    if sheet is None or not urls:
        return
    for url in urls:
        try:
            cell = sheet.find(url)
            if cell:
                sheet.update_cell(cell.row, cell.col + 1, 1)
        except Exception as e:
            logging.error(f"Update sheet error: {e}")

# ── メイン処理 ─────────────────────────────
def main():
    # 1) new_rows_count.txt を読み込んで“新規ゼロ”をチェック
    try:
        cnt = int(open('new_rows_count.txt', encoding='utf-8').read().strip())
    except Exception:
        cnt = -1

    if cnt == 0:
        logging.warning("No new rows; sending greeting tweet.")
        tweet("こんにちは！")
        return

    # 2) それ以外は pending を取得して通常ツイート
    pending = get_pending(sheet)
    if not pending:
        logging.warning("No pending events; sending greeting tweet.")
        tweet("こんにちは！")
        return

    tweeted = []
    for row in pending:
        url     = row.get('URL', '').strip()
        comment = row.get('コメント', '').strip()
        text    = f"{comment} {url}".strip()
        if text and tweet(text):
            tweeted.append(url)

    # 3) フラグ更新
    mark_as_done(sheet, tweeted)

# ── エントリポイント ─────────────────────────
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        traceback.print_exc()
        tweet("こんにちは！")
        sys.exit(1)
