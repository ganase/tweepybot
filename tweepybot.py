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

# ── ロギング ─────────────────────────
logging.basicConfig(
    filename='tweetbot.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info("Logging configured")

# ── Google Sheets 認証 ────────────────
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
    sheet = None  # 後で失敗判定に使う

# ── Twitter 認証 ──────────────────────
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

# ── ユーティリティ ───────────────────
def tweet(text: str):
    try:
        resp = twitter_client.create_tweet(text=text)
        tweet_id = resp.data['id']
        logging.info(f"Tweeted: {text} (id={tweet_id})")
        return tweet_id
    except Exception as e:
        logging.error(f"Tweet failed: {e}")
        return None

def get_pending(sheet, today_str, weekday, ampm):
    if sheet is None:
        return []
    try:
        records = sheet.get_all_records()
    except Exception as e:
        logging.error(f"Sheet fetch error: {e}")
        return []

    pending = []
    for row in records:
        try:
            if row['完了'] != 1 and (
                (row['日付'] == today_str) or
                (not row['日付'] and int(row['曜日']) == weekday and int(row['AMPM']) == ampm)
            ):
                pending.append(row)
        except KeyError:
            logging.error("Spreadsheet headers mismatch")
            return []
    return pending

def mark_as_done(sheet, urls):
    if sheet is None or not urls:
        return
    try:
        for url in urls:
            cell = sheet.find(url)
            if cell:
                sheet.update_cell(cell.row, cell.col + 1, 1)
    except Exception as e:
        logging.error(f"Update sheet error: {e}")

# ── メイン処理 ────────────────────────
def main():
    today = datetime.datetime.today()
    today_str = today.strftime('%Y/%m/%d')
    weekday   = today.weekday()
    ampm      = 0 if today.hour < 12 else 1

    pending = get_pending(sheet, today_str, weekday, ampm)

    # スクレイピング or シート取得失敗時
    if not pending:
        logging.warning("No info fetched; sending failure tweet.")
        tweet("Failed to get information")
        return

    tweeted = []
    for row in pending:
        url = row['URL']
        comment = row['コメントjp']
        if tweet(f"{comment} {url}"):
            tweeted.append(url)

    mark_as_done(sheet, tweeted)

# ── エントリポイント ──────────────────
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        traceback.print_exc()
        tweet("Failed to get information")
        sys.exit(1)
