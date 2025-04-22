#!/usr/bin/env python
# coding: utf-8

import os
import pandas as pd
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

def tweet(text: str):
    try:
        resp = twitter_client.create_tweet(text=text)
        logging.info(f"Tweeted: {text}")
        return True
    except Exception as e:
        logging.error(f"Tweet failed: {e}")
        return False

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
    '1RAZwuhJkpkca4QaVLVO9fzW68TKqLTxIhSfhrGR1Jjw/edit'
)
try:
    spreadsheet = client.open_by_url(SPREADSHEET_URL)
    sheet = spreadsheet.sheet1
except Exception as e:
    logging.error(f"Unable to open spreadsheet: {e}")
    sheet = None

# ── 投稿対象取得 ────────────────────────────
def get_pending(sheet):
    if sheet is None:
        return []
    try:
        records = sheet.get_all_records()
    except Exception as e:
        logging.error(f"Sheet fetch error: {e}")
        return []
    # 完了フラグが 0 の行
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
    # ① スクレイピング結果 CSV が空なら挨拶して終了
    if os.path.exists('event_details.csv'):
        df = pd.read_csv('event_details.csv')
        if df.empty:
            logging.warning("No events scraped; sending greeting tweet.")
            tweet("こんにちは！")
            return

    # ② それ以外は従来の pending → ツイート処理
    pending = get_pending(sheet)
    if not pending:
        logging.warning("No pending events; sending greeting tweet.")
        tweet("こんにちは！")
        return

    tweeted = []
    for row in pending:
        url = row.get('URL', '').strip()
        comment = row.get('コメントjp', '').strip()
        text = f"{comment} {url}".strip()
        if text and tweet(text):
            tweeted.append(url)

    mark_as_done(sheet, tweeted)

# ── エントリポイント ───────────────────────
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        traceback.print_exc()
        tweet("本日はお知らせはないドン！ No new upcoming event today!")
        sys.exit(1)
