#!/usr/bin/env python
# coding: utf-8

import os
import importlib
import csv
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ── 1) プラグインのロード ─────────────────────────
# 環境変数 CLIENT で "cl0001" / "cl0002" / ... を指定
CLIENT = os.environ.get("CLIENT", "cl0001")
module_name = f"plugins.{CLIENT}"
try:
    plugin = importlib.import_module(module_name)
    event_details = plugin.scrape()
    print(f"[INFO] Loaded plugin for CLIENT={CLIENT}, scraped {len(event_details)} events")
except ImportError:
    print(f"[WARN] Plugin not found: {module_name}")
    event_details = []

# ── 2) CSV に書き出し ───────────────────────────────
csv_file = "event_details.csv"
columns  = ["URL", "完了", "コメント", "曜日", "AMPM", "日付", "date"]
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(event_details)
print(f"[INFO] CSV file '{csv_file}' has been created.")

# ── 3) new_rows_count.txt に件数を記録 ─────────────────
with open("new_rows_count.txt", "w", encoding="utf-8") as f:
    f.write(str(len(event_details)))
print(f"[INFO] new_rows_count.txt written ({len(event_details)})")

# ── 4) Google Sheets 書き込み部 ───────────────────────
# 認証
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds  = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gclient = gspread.authorize(creds)

# 環境変数で渡されたシート URL
SPREADSHEET_URL = os.environ["SPREADSHEET_URL"]
spreadsheet = gclient.open_by_url(SPREADSHEET_URL)

# gid 指定なしなら先頭シートを使う
sheet = spreadsheet.sheet1

# 既存の URL を取得
existing = sheet.get_all_records()
existing_urls = {row["URL"] for row in existing}

# CSV から新規行だけ抽出
df = pd.read_csv(csv_file)
new_rows = [row.tolist() for _, row in df.iterrows() if row["URL"] not in existing_urls]

if new_rows:
    sheet.append_rows(new_rows)
    print(f"[INFO] Google Sheets に {len(new_rows)} 行追加されました。")
else:
    print("[INFO] Google Sheets への追加対象はありませんでした。")
