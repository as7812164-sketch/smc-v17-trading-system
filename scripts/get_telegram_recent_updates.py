import os
import sys
import json
import urllib.request
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import get_setting
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

token = get_setting("telegram_bot_token", TELEGRAM_BOT_TOKEN) or TELEGRAM_BOT_TOKEN
chat_id = get_setting("telegram_chat_id", TELEGRAM_CHAT_ID) or TELEGRAM_CHAT_ID

print(f"Checking Telegram Bot Token: {token[:10]}... | Chat ID: {chat_id}")

import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. getMe
try:
    url = f"https://api.telegram.org/bot{token}/getMe"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        me = json.loads(resp.read().decode('utf-8'))
        print("Bot Info:", me)
except Exception as e:
    print("getMe Error:", e)

# 2. getUpdates
try:
    url = f"https://api.telegram.org/bot{token}/getUpdates?limit=20&allowed_updates=[\"message\",\"channel_post\"]"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        updates = json.loads(resp.read().decode('utf-8'))
        results = updates.get("result", [])
        print(f"\nRecent Telegram Updates count: {len(results)}")
        for u in results:
            msg = u.get("message") or u.get("channel_post") or {}
            sender = msg.get("from", {}).get("first_name", "Unknown")
            text = msg.get("text", "")[:80]
            date = msg.get("date")
            print(f"  UpdateID: {u.get('update_id')} | Date: {date} | From: {sender} | Text: {text}")
except Exception as e:
    print("getUpdates Error:", e)
