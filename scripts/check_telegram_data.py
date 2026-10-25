import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import get_connection
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

conn = get_connection()
settings = conn.execute("SELECT * FROM settings").fetchall()
print("SETTINGS:")
for s in settings:
    k, v = s['key'], s['value']
    if 'token' in k.lower() or 'key' in k.lower():
        print(f"  {k}: {v[:8]}...{v[-4:] if len(v)>12 else ''}")
    else:
        print(f"  {k}: {v}")

print(f"\nENV TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN[:8] if TELEGRAM_BOT_TOKEN else 'EMPTY'}...")
print(f"ENV TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")

sent_alerts = conn.execute("SELECT * FROM sent_alerts ORDER BY sent_at DESC LIMIT 30").fetchall()
print(f"\nSENT ALERTS IN DB ({len(sent_alerts)}):")
for a in sent_alerts:
    print(f"  Key: {a['alert_key']} | Sym: {a['symbol']} | Side: {a['side']} | SentAt: {a['sent_at']} | MsgId: {a['msg_id']}")

journal = conn.execute("SELECT * FROM trade_journal ORDER BY timestamp DESC LIMIT 20").fetchall()
print(f"\nTRADE JOURNAL IN DB ({len(journal)}):")
for j in journal:
    print(f"  {dict(j)}")
