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
logging.info("Logging is configured correctly.")

# ── Google Sheets 認証 ────────────────────
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
spreadsheet_url = os.environ.get("SPREADSHEET_URL")  # matrix でセット済み
spreadsheet = client.open_by_url(spreadsheet_url)
sheet = spreadsheet.sheet1

# ── Twitter 認証 ──────────────────────────
def load_twitter_keys(json_path):
    with open(json_path, mode='r', encoding='utf-8') as f:
        return json.load(f)

twitter_keys = load_twitter_keys('twitter_key.json')
twitter_client = tweepy.Client(
    bearer_token=twitter_keys['BEARER_TOKEN'],
    consumer_key=twitter_keys['CONSUMER_KEY'],
    consumer_secret=twitter_keys['CONSUMER_SECRET'],
    access_token=twitter_keys['ACCESS_TOKEN'],
    access_token_secret=twitter_keys['ACCESS_SECRET']
)

# ── 未完了URL取得 ──────────────────────────
def get_pending_urls(sheet, current_date, current_day, ampm):
    pending = []
    try:
        records = sheet.get_all_records()
        for row in records:
            if row['完了'] != 1 and (
                (row['日付'] == current_date) or
                (not row['日付'] and int(row['曜日']) == current_day and int(row['AMPM']) == ampm)
            ):
                pending.append(row)
    except Exception as e:
        logging.error(f"Error loading pending URLs: {e}")
    return pending

# ── URLをツイート ──────────────────────────
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
    today = datetime.datetime.today()
    current_date = today.strftime('%Y/%m/%d')
    current_day  = today.weekday()
    ampm         = 0 if today.hour < 12 else 1

    pending_urls = get_pending_urls(sheet, current_date, current_day, ampm)
    logging.info(f"Pending URLs: {pending_urls}")

    # ←ここを追加：対象が一件もなければフォールバックツイート
    if not pending_urls:
        logging.info("No pending URLs; sending default tweet.")
        tweet_url(
            "https://usergroups.tableau.com/events/#/list",
            "本日はお知らせはないドン！次のサイトをチェックドン！"
        )
        return

    tweeted = []
    for row in pending_urls:
        url     = row['URL'].strip()
        comment = row.get('コメントjp', row.get('コメント', '')).strip()
        if tweet_url(url, comment):
            tweeted.append(url)

    if tweeted:
        mark_as_done(sheet, tweeted)
        logging.info(f"Marked as done: {tweeted}")

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
