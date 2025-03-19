#!/usr/bin/env python
# coding: utf-8

# In[5]:


import gspread
from oauth2client.service_account import ServiceAccountCredentials
import tweepy
import datetime
import json
import logging

# ロギングの設定（指定されたディレクトリにログファイルを保存）
logging.basicConfig(
    filename='tweetbot.log',
    level=logging.DEBUG,  # DEBUGレベルに設定してすべてのログをキャプチャ
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ロギングが設定されているか確認するためのメッセージ
logging.info("Logging is configured correctly.")

# Google スプレッドシート API の設定
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
client = gspread.authorize(creds)

# スプレッドシートを開く
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1RAZwuhJkpkca4QaVLVO9fzW68TKqLTxIhSfhrGR1Jjw/edit?usp=sharing'
spreadsheet = client.open_by_url(spreadsheet_url)
sheet = spreadsheet.sheet1

# Twitter APIの設定をjsonファイルから読み込み
def load_twitter_keys(json_path):
    with open(json_path, mode='r', encoding='utf-8') as file:
        keys = json.load(file)
        return keys

# JSONファイルからTwitter APIキーを読み込む
twitter_keys = load_twitter_keys('twitter_key.json')

# Twitter API v2用の認証情報
BEARER_TOKEN = twitter_keys['BEARER_TOKEN']
CONSUMER_KEY = twitter_keys['CONSUMER_KEY']
CONSUMER_SECRET = twitter_keys['CONSUMER_SECRET']
ACCESS_TOKEN = twitter_keys['ACCESS_TOKEN']
ACCESS_SECRET = twitter_keys['ACCESS_SECRET']

# Tweepyのクライアントを設定（Twitter API v2用）
twitter_client = tweepy.Client(bearer_token=BEARER_TOKEN,
                               consumer_key=CONSUMER_KEY,
                               consumer_secret=CONSUMER_SECRET,
                               access_token=ACCESS_TOKEN,
                               access_token_secret=ACCESS_SECRET)

# 完了していないURLを取得
def get_pending_urls(sheet, current_date, current_day, ampm):
    pending_urls = []
    try:
        records = sheet.get_all_records()
        logging.debug(f"Records from spreadsheet: {records}")
        for row in records:
            # 日付が優先、次に曜日と時間帯をチェック
            if row['完了'] != 1 and (
                (row['日付'] == current_date) or 
                (not row['日付'] and int(row['曜日']) == current_day and int(row['AMPM']) == ampm)
            ):
                pending_urls.append(row)
        logging.info(f"Pending URLs loaded successfully: {pending_urls}")
    except KeyError as e:
        logging.error(f"KeyError: {e}. Check if the spreadsheet has the correct headers.")
    except Exception as e:
        logging.error(f"An error occurred while loading pending URLs: {e}")
    return pending_urls

# URLとコメントをツイートする
def tweet_url(url, comment):
    tweet_text = f"{comment} {url}"
    try:
        response = twitter_client.create_tweet(text=tweet_text)
        tweet_id = response.data['id']
        logging.info(f"Successfully tweeted: '{tweet_text}' with Tweet ID: {tweet_id}")
        return tweet_id
    except tweepy.TweepyException as e:
        logging.error(f"Error tweeting: '{tweet_text}': {e.response.text}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred when tweeting: '{tweet_text}': {e}")
        return None

# スプレッドシートを更新
def mark_as_done(sheet, tweeted_urls):
    try:
        records = sheet.get_all_records()
        logging.info(f"Updating spreadsheet for URLs: {tweeted_urls}")
        for i, row in enumerate(records):
            if row['URL'] in tweeted_urls:
                # 行を見つけて完了フラグを更新
                cell = sheet.find(row['URL'])
                if cell:
                    complete_cell = sheet.cell(cell.row, cell.col + 1)
                    logging.info(f"Updating cell at row {cell.row}, col {cell.col + 1} (current value: {complete_cell.value}) to 1")
                    sheet.update_cell(cell.row, cell.col + 1, 1)  # 完了列を更新
        logging.info("Spreadsheet updated successfully.")
    except Exception as e:
        logging.error(f"An error occurred while updating the spreadsheet: {e}")

# 毎日実行し、実行日の条件に一致するURLをツイート
def main():
    current_date = datetime.datetime.today().strftime('%Y/%m/%d')  # 今日の日付を取得
    current_day = datetime.datetime.today().weekday()  # 今日の曜日を取得
    current_hour = datetime.datetime.now().hour
    ampm = 0 if current_hour < 12 else 1  # 午前なら0、午後なら1

    pending_urls = get_pending_urls(sheet, current_date, current_day, ampm)
    logging.info(f"Pending URLs to tweet: {pending_urls}")
    tweeted_urls = []
    for row in pending_urls:
        url = row['URL']
        comment = row['コメントjp']
        logging.info(f"Attempting to tweet URL: {url} with comment: {comment}")
        tweet_id = tweet_url(url, comment)
        if tweet_id:
            tweeted_urls.append(url)
        else:
            logging.error(f"Failed to tweet URL: {url}")
    if tweeted_urls:
        mark_as_done(sheet, tweeted_urls)
        logging.info(f"Updated spreadsheet after tweeting URLs: {tweeted_urls}")

if __name__ == "__main__":
    main()

