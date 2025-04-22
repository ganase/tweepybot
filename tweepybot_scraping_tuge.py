#!/usr/bin/env python
# coding: utf-8

import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pytz

# ── スクレイピング部 ──────────────────────────────────
# 日本時間の日付文字列を生成
jst = pytz.timezone('Asia/Tokyo')
now_jst = datetime.now(jst).strftime('%Y/%m/%d')

chrome_options = Options()
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--headless")
chrome_options.binary_location = '/usr/bin/chromium-browser'
driver = webdriver.Chrome(options=chrome_options)

driver.get("https://usergroups.tableau.com/events/#/list")
wait = WebDriverWait(driver, 60)
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "panel-picture-content")))
time.sleep(5)

events = driver.find_elements(By.CLASS_NAME, "panel-picture-content")
event_details = []
for event in events[:5]:
    try:
        date = event.find_element(By.CLASS_NAME, "date").text
        title = event.find_element(By.CLASS_NAME, "general-body--color").text
        link = event.find_element(By.CSS_SELECTOR, "a.EventRectangle-styles-viewDetails-PsfIW")\
                    .get_attribute("href")
        event_details.append({
            "URL": link,
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

# CSV 出力
csv_file = "event_details.csv"
columns = ["URL", "完了", "コメント", "曜日", "AMPM", "日付", "date"]
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(event_details)
print(f"CSV file '{csv_file}' has been created.")

# ── Google Sheets 書き込み部 ──────────────────────────────────
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 認証設定
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# スプレッドシート URL
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1RAZwuhJkpkca4QaVLVO9fzW68TKqLTxIhSfhrGR1Jjw/edit"

spreadsheet = client.open_by_url(SPREADSHEET_URL)

# gid でシートを探す（見つからなければ先頭シートを使う）
target_gid = 803084007
sheet = None
for ws in spreadsheet.worksheets():
    if ws.id == target_gid:
        sheet = ws
        break
if sheet is None:
    sheet = spreadsheet.sheet1

# 既存 URL リスト取得
existing = sheet.get_all_records()
existing_urls = {row['URL'] for row in existing}

# 新規行の抽出
df = pd.read_csv(csv_file)
new_rows = [row.tolist() for _, row in df.iterrows() if row['URL'] not in existing_urls]

if new_rows:
    sheet.append_rows(new_rows)
    print("Google Sheets に新しい行が追加されました。")
else:
    print("Google Sheets への追加対象はありませんでした。")
