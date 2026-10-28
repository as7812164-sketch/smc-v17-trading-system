"""
INSTITUTIONAL ALERT & WEBHOOK AUTOMATION ENGINE (PHASE 7)
Handles:
- Custom Price, CVD Absorption & SMC Zone Alert triggers
- Live Ticker threshold verification
- Telegram Push Alert dispatch
- Custom Webhook JSON Payload dispatch
- JSON Persistence in database/user_alerts.json
"""

import os
import json
import time
import uuid
import asyncio
import pathlib
import urllib.request
from typing import Dict, Any, List, Optional

BASE_DIR = pathlib.Path(__file__).parent.parent
ALERTS_FILE = BASE_DIR / "database" / "user_alerts.json"

_ALERTS_CACHE: List[Dict[str, Any]] = []

def _load_alerts() -> List[Dict[str, Any]]:
    global _ALERTS_CACHE
    if not ALERTS_FILE.exists():
        _ALERTS_CACHE = []
        return _ALERTS_CACHE
    try:
        with open(ALERTS_FILE, "r", encoding="utf-8") as f:
            _ALERTS_CACHE = json.load(f)
    except Exception:
        _ALERTS_CACHE = []
    return _ALERTS_CACHE

def _save_alerts():
    global _ALERTS_CACHE
    try:
        ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            json.dump(_ALERTS_CACHE, f, indent=2)
    except Exception as e:
        print(f"Error saving alerts: {e}")

def get_all_alerts() -> List[Dict[str, Any]]:
    return _load_alerts()

def create_user_alert(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    global _ALERTS_CACHE
    _load_alerts()
    alert_id = str(uuid.uuid4())[:8]
    new_alert = {
        "id": alert_id,
        "symbol": alert_data.get("symbol", "BTCUSDT").upper(),
        "condition": alert_data.get("condition", "CROSS_ABOVE"),  # CROSS_ABOVE, CROSS_BELOW, CVD_DIVERGENCE, SMC_ZONE
        "target_price": float(alert_data.get("target_price", 0.0)),
        "current_price": float(alert_data.get("current_price", 0.0)),
        "sound": bool(alert_data.get("sound", True)),
        "telegram": bool(alert_data.get("telegram", True)),
        "webhook_url": alert_data.get("webhook_url", "").strip(),
        "note": alert_data.get("note", "Institutional Price Trigger"),
        "status": "ACTIVE",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "triggered_at": None
    }
    _ALERTS_CACHE.append(new_alert)
    _save_alerts()
    return new_alert

def delete_user_alert(alert_id: str) -> bool:
    global _ALERTS_CACHE
    _load_alerts()
    initial_len = len(_ALERTS_CACHE)
    _ALERTS_CACHE = [a for a in _ALERTS_CACHE if a.get("id") != alert_id]
    if len(_ALERTS_CACHE) != initial_len:
        _save_alerts()
        return True
    return False

async def dispatch_webhook_payload(url: str, payload: Dict[str, Any]) -> bool:
    if not url:
        return False
    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json", "User-Agent": "Antigravity-Alert-Webhook/1.0"},
            method="POST"
        )
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=5))
        return True
    except Exception as e:
        print(f"Webhook dispatch failed: {e}")
        return False

async def send_alert_notification(alert: Dict[str, Any], trigger_price: float):
    sym = alert.get("symbol", "")
    cond = alert.get("condition", "")
    target = alert.get("target_price", 0.0)
    note = alert.get("note", "")

    # 1. Telegram
    if alert.get("telegram"):
        try:
            from alerts.telegram_service import telegram_service
            msg = (
                f"🚨 <b>INSTITUTIONAL ALERT TRIGGERED</b>\n\n"
                f"🪙 <b>Symbol:</b> #{sym}\n"
                f"🎯 <b>Condition:</b> {cond}\n"
                f"💲 <b>Target:</b> ${target:,.4f}\n"
                f"⚡ <b>Trigger Price:</b> ${trigger_price:,.4f}\n"
                f"📝 <b>Note:</b> {note}\n"
                f"⏰ <b>Time:</b> {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
            )
            await telegram_service.send_text_alert(msg)
        except Exception as e:
            print(f"Telegram alert delivery error: {e}")

    # 2. Custom Webhook
    webhook_url = alert.get("webhook_url")
    if webhook_url:
        payload = {
            "event": "ALERT_TRIGGERED",
            "alert_id": alert.get("id"),
            "symbol": sym,
            "condition": cond,
            "target_price": target,
            "trigger_price": trigger_price,
            "note": note,
            "timestamp": time.time()
        }
        await dispatch_webhook_payload(webhook_url, payload)

def check_price_alerts(symbol_prices: Dict[str, float]) -> List[Dict[str, Any]]:
    global _ALERTS_CACHE
    _load_alerts()
    triggered = []
    changed = False

    for a in _ALERTS_CACHE:
        if a.get("status") != "ACTIVE":
            continue
        sym = a.get("symbol", "")
        cur_p = symbol_prices.get(sym)
        if not cur_p:
            continue

        cond = a.get("condition")
        target = float(a.get("target_price", 0.0))
        is_hit = False

        if cond == "CROSS_ABOVE" and cur_p >= target:
            is_hit = True
        elif cond == "CROSS_BELOW" and cur_p <= target:
            is_hit = True

        if is_hit:
            a["status"] = "TRIGGERED"
            a["triggered_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            a["trigger_price"] = cur_p
            triggered.append(a)
            changed = True

    if changed:
        _save_alerts()

    return triggered
