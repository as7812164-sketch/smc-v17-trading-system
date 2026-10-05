import os
import sys
import sqlite3
import urllib.request
import json
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from database.db import reset_paper_account, reset_compounding_sections, get_compounding_sections, get_connection

def clean_local_db():
    print("--- 1. CLEANING & RESETTING LOCAL DATABASE ---")
    reset_compounding_sections(50.0)
    reset_paper_account(50.0)
    with get_connection() as conn:
        conn.execute("DELETE FROM paper_trades")
        try:
            conn.execute("DELETE FROM trade_journal")
        except Exception:
            pass
        conn.commit()

    sections = get_compounding_sections()
    print(f"Total sections: {len(sections.get('sections', []))}")
    for s in sections.get('sections', []):
        print(f"Section {s['id']}: {s['name']} | Balance: ${s['current_balance']} | Mode: {s.get('mode')}")

def clean_render_cloud():
    print("\n--- 2. RESETTING RENDER CLOUD DATABASE ---")
    url = "https://smc-ai-agent.onrender.com/api/paper/sections/reset"
    try:
        req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            print("Render sections reset response:", data.get("status", "ok"))
    except Exception as e:
        print("Render sections reset notice:", e)

    url2 = "https://smc-ai-agent.onrender.com/api/paper/reset"
    try:
        req = urllib.request.Request(url2, data=json.dumps({"starting_balance": 50.0}).encode(), headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            print("Render paper reset response:", data.get("status", "ok"))
    except Exception as e:
        print("Render paper reset notice:", e)

if __name__ == "__main__":
    clean_local_db()
    clean_render_cloud()
