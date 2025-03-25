#!/usr/bin/env python
# coding: utf-8

# ## Tableau user group upcoming eventから記事のスクレイピング

# In[9]:


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
chrome_options.add_argument("--headless")  # GUIを表示しないモード

driver = webdriver.Chrome(options=chrome_options)

# Tableau User Groupsのイベントページを開く
driver.get("https://usergroups.tableau.com/events/#/list")

# イベントリストが読み込まれるまで待機
wait = WebDriverWait(driver, 60)  # タイムアウト時間を60秒に設定
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "panel-picture-content")))

# イベントが完全に読み込まれるまで待機
time.sleep(10)  # 追加の待機時間を設定

# イベントが読み込まれるのを待つ
events = driver.find_elements(By.CLASS_NAME, "panel-picture-content")

# 最初の5つのイベント情報を抽出
event_details = []
for event in events[:5]:
    try:
        date_element = event.find_element(By.CLASS_NAME, "date")
        date = date_element.text
        
        # タイトル要素の取得
        title_element = event.find_element(By.CLASS_NAME, "general-body--color")
        title = title_element.text
        
        # 詳細リンクの取得
        details_element = event.find_element(By.CSS_SELECTOR, "a.EventRectangle-styles-viewDetails-PsfIW")
        details_link = details_element.get_attribute("href")
        
        # ベースURLと詳細リンクの結合
        base_url = ""
        full_url = base_url + details_link
        
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

# ドライバーを閉じる
driver.quit()

# CSVファイルに書き込む
csv_file = "event_details.csv"
csv_columns = ["URL", "完了", "コメント", "曜日", "AMPM", "日付","date"]

try:
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for data in event_details:
            writer.writerow(data)
except IOError:
    print("I/O error")

print(f"CSV file '{csv_file}' has been created.")


# ## Google sheets にスクレイピング結果を書き込み

# In[13]:


import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Google Sheets APIの認証情報を設定
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('servic"redentials.json scope)
client = gspread.authorize(creds)

# Google Sheetsの指定されたシートを開く
spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1RAZwuhJkpkca4QaVLVO9fzW68TKqLTxIhSfhrGR1Jjw/edit")
sheet = spreadsheet.sheet1

# Google Sheetsのデータを取得
existing_data = sheet.get_all_records()
existing_urls = [row['URL'] for row in existing_data]

# CSVファイルのデータを読み込む
csv_file = "event_details.csv"
df = pd.read_csv(csv_file)

# Google Sheetsに存在しないURLの行を追加
new_rows = []
for _, row in df.iterrows():
    if row['URL'] not in existing_urls:
        new_rows.append(row.tolist())

if new_rows:
    sheet.append_rows(new_rows)

print("Google Sheetsに新しい行が追加されました。")

