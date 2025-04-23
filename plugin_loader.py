#!/usr/bin/env python
# coding: utf-8

import os
import importlib
import csv
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ── 1) プラグインをロード ─────────────────────────────────
CLIENT = os.environ.get("CLIENT", "cl0001")
module_name = f"plugins.{CLIENT}"
try:
    plugin = importlib.import_module(module_name)
    event_details = plugin.scrape()
    print(f"[INFO] Loaded plugin for CLIENT={CLIENT}, scraped {len(event_details)} events")
except ImportError:
    print(f"[WARN] Plugin not found: {module_name}")
    event_details = []

# ── 2) CSV に書き出し ─────────────────────────────────────
csv_file = "event_details.csv"
columns  = ["URL", "完了", "コメントjp", "曜日", "AMPM", "日付", "date"]
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(event_details)
print(f"[INFO] CSV file '{csv_file}' has been created.")

# ── 3) new_rows_count.txt に件数を記録 ─────────────────────────
# Google Sheets から既存 URL を取得して比較
SPREADSHEET_URL = os.environ.get("SPREADSHEET_URL", "")
# 対象シートの gid を環境変数で指定する場合は GID 環境変数を使用
TARGET_GID = int(os.environ.get("GID", 803084007))

# 認証設定
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gclient = gspread.authorize(creds)

# シート選択（gid 優先、なければ先頭シート）
spreadsheet = gclient.open_by_url(SPREADSHEET_URL)
sheet = None
for ws in spreadsheet.worksheets():
    if ws.id == TARGET_GID:
        sheet = ws
        break
if sheet is None:
    sheet = spreadsheet.sheet1

# 既存 URL を取得
existing = sheet.get_all_records()
existing_urls = {row["URL"] for row in existing}

df = pd.read_csv(csv_file)
new_rows = [row.tolist() for _, row in df.iterrows() if row["URL"] not in existing_urls]

with open("new_rows_count.txt", "w", encoding="utf-8") as f:
    f.write(str(len(new_rows)))
print(f"[INFO] new_rows_count.txt written ({len(new_rows)})")

# ── 4) Google Sheets 書き込み部 ─────────────────────────────
if SPREADSHEET_URL and new_rows:
    # 対象シート再取得
    spreadsheet = gclient.open_by_url(SPREADSHEET_URL)
    # sheet は先に取得済み
    if not sheet:
        sheet = spreadsheet.sheet1
    sheet.append_rows(new_rows)
    print(f"[INFO] Google Sheets に {len(new_rows)} 行追加されました。")
elif SPREADSHEET_URL:
    print("[INFO] Google Sheets への追加対象はありませんでした。")
else:
    print("[WARN] SPREADSHEET_URL が設定されていないため、Sheets 書き込みをスキップしました。")
