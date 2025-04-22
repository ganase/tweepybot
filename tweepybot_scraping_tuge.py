#!/usr/bin/env python
# coding: utf-8

# ## Tableau user group upcoming eventから記事のスクレイピング

import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pytz

# 現在日付を日本時間に変換
jst = pytz.timezone('Asia/Tokyo')
now_jst = datetime.now(jst).strftime('%Y/%m/%d')

# Chromeオプションの設定
chrome_options = Options()
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--headless")
chrome_options.binary_location = '/usr/bin/chromium-browser'
driver = webdriver.Chrome(options=chrome_options)

# Tableau User Groupsのイベントページを開く
driver.get("https://usergroups.tableau.com/events/#/list")

# イベントリストが読み込まれるまで待機
wait = WebDriverWait(driver, 60)
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "panel-picture-content")))
time.sleep(10)

# イベント情報を抽出
events = driver.find_elements(By.CLASS_NAME, "panel-picture-content")
event_details = []
for event in events[:5]:
    try:
        date = event.find_element(By.CLASS_NAME, "date").text
        title = event.find_element(By.CLASS_NAME, "general-body--color").text
        link = event.find_element(By.CSS_SELECTOR, "a.EventRectangle-styles-viewDetails-PsfIW").get_attribute("href")
        full_url = link  # href が絶対URLならそのまま。相対URLなら base を補う

        event_details.append({
            "URL": full_url,
            "完了": 0,
            "コメント": title,
            "曜日": 0,
            "AMPM": 0,
            "日付": now_jst,
            "date": date
        })
    except Exception as e:
        print(f"Error extracting event details: {e}")

driver.quit()

# CSVに書き出し
csv_file = "event_details.csv"
csv_columns = ["URL", "完了", "コメント", "曜日", "AMPM", "日付", "date"]
try:
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for data in event_details:
            writer.writerow(data)
except IOError:
    print("I/O error")
print(f"CSV file '{csv_file}' has been created.")

# ## Google Sheets にスクレイピング結果を書き込み
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 認証設定
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# 対象スプレッドシートを開く
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1RAZwuhJkpkca4QaVLVO9fzW68TKqLTxIhSfhrGR1Jjw/edit#gid=803084007"
spreadsheet = client.open_by_url(SPREADSHEET_URL)

# ←ここを sheet1 から「2番目のシート」へ変更
sheet = spreadsheet.get_worksheet(1)  # index=1 が 2番目のタブ

# 既存データを取得
existing_data = sheet.get_all_records()
existing_urls = [row['URL'] for row in existing_data]

# CSVを読み込み、新規URLだけを抽出して追加
df = pd.read_csv(csv_file)
new_rows = [row.tolist() for _, row in df.iterrows() if row['URL'] not in existing_urls]

if new_rows:
    sheet.append_rows(new_rows)
    print("Google Sheets に新しい行が追加されました。")
else:
    print("Google Sheets への追加対象はありませんでした。")
