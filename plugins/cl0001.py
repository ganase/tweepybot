#!/usr/bin/env python
# coding: utf-8

import pytz
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape():
    # ── スクレイピング部 ────────────────────────────
    jst      = pytz.timezone('Asia/Tokyo')
    now_jst  = datetime.now(jst).strftime('%Y/%m/%d')

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
    for ev in events[:5]:
        try:
            date_text = ev.find_element(By.CLASS_NAME, "date").text
            title     = ev.find_element(By.CLASS_NAME, "general-body--color").text
            link      = ev.find_element(
                By.CSS_SELECTOR,
                "a.EventRectangle-styles-viewDetails-PsfIW"
            ).get_attribute("href")
            event_details.append({
                "URL":        link,
                "完了":       0,
                "コメントjp": title,
                "曜日":       0,
                "AMPM":       0,
                "日付":       now_jst,
                "date":       date_text
            })
        except Exception as e:
            print(f"Error extracting event: {e}")

    driver.quit()
    return event_details
