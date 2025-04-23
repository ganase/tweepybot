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
# 新規追加行数(new_rows)を記録するよう修正
# まず、CSV を読み込み既存 URL をチェック
SPREADSHEET_URL = os.environ.get("SPREADSHEET_URL", "")
# Google Sheets 接続用に認証だけ行い、一時的にシート情報を取得
# ※ 詳細な書き込み処理は後述するため、ここでは既存 URLs 抽出のみ実施
creds_scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", creds_scope)
gclient = gspread.authorize(creds)
spreadsheet = gclient.open_by_url(SPREADSHEET_URL)
sheet = spreadsheet.sheet1
existing = sheet.get_all_records()
existing_urls = {row["URL"] for row in existing}

df = pd.read_csv(csv_file)
new_rows = [row.tolist() for _, row in df.iterrows() if row["URL"] not in existing_urls]

with open("new_rows_count.txt", "w", encoding="utf-8") as f:
    f.write(str(len(new_rows)))
print(f"[INFO] new_rows_count.txt written ({len(new_rows)})")

# ── 4) Google Sheets 書き込み部 ─────────────────────────────
if SPREADSHEET_URL:
    # 認証
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", creds_scope)
    gclient = gspread.authorize(creds)
    spreadsheet = gclient.open_by_url(SPREADSHEET_URL)
    sheet = spreadsheet.sheet1

    if new_rows:
        sheet.append_rows(new_rows)
        print(f"[INFO] Google Sheets に {len(new_rows)} 行追加されました。")
    else:
        print("[INFO] Google Sheets への追加対象はありませんでした。")
else:
    print("[WARN] SPREADSHEET_URL が設定されていないため、Sheets 書き込みをスキップしました。")
