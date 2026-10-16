"""
BB 3.0 REAL-TIME CANDLESTICK CHART GENERATOR FOR TELEGRAM ALERTS
================================================================
Generates high-resolution, institutional dark-theme TradingView-style candlestick
charts for BB 3.0 alerts with real market candles, PDH/PDL liquidity anchors,
15m Extreme Order Blocks, 50% Mean Threshold Limit Entry, Anti-Hunt Stop Loss,
and the Stepped Trailing Profit Armor Ladder.
"""

import io
import os
import sys
import ssl
import json
import uuid
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.dates as mdates

def generate_bb30_chart(
    symbol: str,
    candles: List[Dict[str, Any]],
    setup: Dict[str, Any],
    limit_bars: int = 45
) -> bytes:
    """
    Renders real candlestick price action with complete BB 3.0 strategy annotations.
    Returns PNG bytes.
    """
    # Slice to recent bars
    recent_candles = candles[-limit_bars:] if len(candles) > limit_bars else candles
    if len(recent_candles) < 5:
        return b""

    side = setup.get("side", "LONG").upper()
    is_long = side in ("LONG", "BUY")
    anchor_name = setup.get("anchor_name", "PDL" if is_long else "PDH")
    anchor_price = float(setup.get("anchor_price") or 0.0)
    ob_top = float(setup.get("ob_top") or 0.0)
    ob_bottom = float(setup.get("ob_bottom") or 0.0)
    mt_entry = float(setup.get("mt_entry") or 0.0)
    sl_price = float(setup.get("sl") or setup.get("active_sl") or 0.0)
    t1 = float(setup.get("target_1r") or 0.0)
    t15 = float(setup.get("target_15r") or 0.0)
    t3 = float(setup.get("target_3r") or 0.0)
    sec_id = setup.get("section_id", 1)
    status_label = setup.get("status_label", "PENDING LIMIT SETUP")
    active_sl = float(setup.get("active_sl") or 0.0)
    current_tier = int(setup.get("current_tier") or 0)

    # Determine Price Scale
    min_p = min(c["low"] for c in recent_candles)
    max_p = max(c["high"] for c in recent_candles)

    # Include key levels in scale
    all_levels = [min_p, max_p]
    for lev in [anchor_price, ob_top, ob_bottom, mt_entry, sl_price, t1, t15]:
        if lev > 0:
            all_levels.append(lev)
    pad = (max(all_levels) - min(all_levels)) * 0.08
    y_min = max(0, min(all_levels) - pad)
    y_max = max(all_levels) + pad

    # Figure Setup
    fig, ax = plt.subplots(figsize=(12, 6.8), facecolor='#080B11', dpi=130)
    ax.set_facecolor('#0B0E14')

    # Grid styling
    ax.grid(True, linestyle='--', alpha=0.15, color='#334155')

    n_bars = len(recent_candles)
    x_indices = list(range(n_bars))

    bull_color = '#00DF9A'  # Bright Teal/Green
    bear_color = '#F43F5E'  # Bright Rose/Red

    # Render Candlesticks
    for i, c in enumerate(recent_candles):
        o = float(c["open"])
        h = float(c["high"])
        l = float(c["low"])
        cl = float(c["close"])

        is_bull = cl >= o
        c_color = bull_color if is_bull else bear_color

        # Upper and Lower Wick
        ax.vlines(x=i, ymin=l, ymax=h, color=c_color, linewidth=1.2, alpha=0.9, zorder=2)

        # Candle Body
        body_height = max(abs(cl - o), (y_max - y_min) * 0.001)
        body_bottom = min(o, cl)
        ax.bar(x=i, height=body_height, bottom=body_bottom, width=0.65, color=c_color, zorder=3)

    # 1. PDH / PDL Liquidity Anchor Line
    if anchor_price > 0:
        ax.axhline(anchor_price, color='#F59E0B', linestyle='--', linewidth=1.6, alpha=0.95, zorder=4)
        ax.text(0.5, anchor_price, f"  * {anchor_name} LIQUIDITY ANCHOR: ${anchor_price:.4f}",
                color='#F59E0B', fontsize=9, fontweight='bold', va='bottom', ha='left',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#1E293B', edgecolor='#F59E0B', alpha=0.85))

    # 2. 15m Extreme Order Block Shaded Zone
    if ob_top > 0 and ob_bottom > 0 and ob_top > ob_bottom:
        ob_color = '#8B5CF6' if is_long else '#EC4899'
        ax.axhspan(ob_bottom, ob_top, color=ob_color, alpha=0.22, zorder=1)
        mid_ob = (ob_top + ob_bottom) / 2.0
        ax.text(n_bars - 1, mid_ob, f" 15m EXTREME OB [${ob_bottom:.4f} - ${ob_top:.4f}] ",
                color='#DDD6FE', fontsize=8, fontweight='bold', va='center', ha='right',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#2E1065', edgecolor=ob_color, alpha=0.8))

    # 3. 50% Mean Threshold (MT) Limit Entry
    if mt_entry > 0:
        ax.axhline(mt_entry, color='#00F0FF', linestyle='-', linewidth=2.0, alpha=0.95, zorder=5)
        ax.text(n_bars - 1, mt_entry, f" [LIMIT ENTRY @ 50% MT]: ${mt_entry:.4f} ",
                color='#000000', fontsize=9, fontweight='bold', va='center', ha='right',
                bbox=dict(boxstyle='round,pad=0.25', facecolor='#00F0FF', edgecolor='none', alpha=0.95))

    # 4. Stop Loss (Anti-Hunt Buffer)
    if sl_price > 0:
        sl_display = active_sl if active_sl > 0 else sl_price
        ax.axhline(sl_display, color='#EF4444', linestyle='-', linewidth=1.8, alpha=0.95, zorder=5)
        sl_label = f" [STOP LOSS] 0.15% Buffer: ${sl_display:.4f} " if current_tier == 0 else f" [ACTIVE TRAILING SL]: ${sl_display:.4f} "
        ax.text(n_bars - 1, sl_display, sl_label,
                color='#FFFFFF', fontsize=9, fontweight='bold', va='center', ha='right',
                bbox=dict(boxstyle='round,pad=0.25', facecolor='#DC2626', edgecolor='none', alpha=0.95))

    # 5. Stepped Trailing Ladder Milestones (+1.0R, +1.5R, +3.0R)
    if t1 > 0:
        ax.axhline(t1, color='#10B981', linestyle=':', linewidth=1.3, alpha=0.85, zorder=4)
        ax.text(0.5, t1, f"  +1.0R Milestone (Move SL to +0.2R BE): ${t1:.4f}",
                color='#10B981', fontsize=8, fontweight='bold', va='bottom', ha='left')

    if t15 > 0:
        ax.axhline(t15, color='#10B981', linestyle='-.', linewidth=1.4, alpha=0.85, zorder=4)
        ax.text(0.5, t15, f"  +1.5R Milestone (Lock +1.0R Pure Profit): ${t15:.4f}",
                color='#10B981', fontsize=8, fontweight='bold', va='bottom', ha='left')

    if t3 > 0:
        ax.axhline(t3, color='#22C55E', linestyle='-', linewidth=1.8, alpha=0.9, zorder=4)
        ax.text(n_bars - 1, t3, f" [TARGET] TAKE PROFIT (+3.0R): ${t3:.4f} ",
                color='#000000', fontsize=9, fontweight='bold', va='center', ha='right',
                bbox=dict(boxstyle='round,pad=0.25', facecolor='#22C55E', edgecolor='none', alpha=0.95))

    # Axis Limits & Ticks
    ax.set_ylim(y_min, y_max)
    ax.set_xlim(-1, n_bars + 1)
    ax.tick_params(colors='#94A3B8', labelsize=8.5)
    for spine in ax.spines.values():
        spine.set_color('#1E293B')

    # Y-axis format
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")

    # X-axis time formatting
    step = max(1, n_bars // 6)
    sampled_indices = list(range(0, n_bars, step))
    if (n_bars - 1) not in sampled_indices:
        sampled_indices.append(n_bars - 1)
    
    time_labels = []
    for idx in sampled_indices:
        t_val = recent_candles[idx].get("time", 0)
        if t_val > 10000000000:  # ms
            t_val /= 1000.0
        dt = datetime.fromtimestamp(t_val, tz=timezone.utc)
        time_labels.append(dt.strftime("%H:%M UTC"))
    ax.set_xticks(sampled_indices)
    ax.set_xticklabels(time_labels, color='#94A3B8', fontsize=8)

    # Title & Subtitle HUD
    side_color = '#00DF9A' if is_long else '#F43F5E'
    title_text = f"BB 3.0 SNIPER  |  #{symbol} 15m  |  {side} (5x Isolated)"
    subtitle_text = f"Strategy: Day 1 {anchor_name} Sweep + 15m Extreme OB Retest  |  Section #{sec_id}  |  Status: {status_label}"
    
    fig.text(0.08, 0.94, title_text, fontsize=12, fontweight='bold', color='#FFFFFF', fontfamily='sans-serif')
    fig.text(0.08, 0.91, subtitle_text, fontsize=9, color='#94A3B8', fontfamily='sans-serif')

    # Save to PNG Buffer
    buf = io.BytesIO()
    plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.89])
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def send_telegram_alert_with_chart(
    token: str,
    chat_id: str,
    caption: str,
    symbol: str,
    candles: List[Dict[str, Any]],
    setup: Dict[str, Any]
) -> bool:
    """
    Renders real candlestick chart and uploads to Telegram via sendPhoto API.
    Falls back gracefully to text message if photo fails.
    """
    if not token or not chat_id:
        return False

    # 1. Generate Real Chart Image
    try:
        chart_bytes = generate_bb30_chart(symbol, candles, setup)
    except Exception as e:
        print(f"[Chart Generation Error]: {e}")
        chart_bytes = b""

    # 2. If chart generation succeeded, send via sendPhoto
    if chart_bytes and len(chart_bytes) > 1000:
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        lines = []

        lines.append(f"--{boundary}".encode())
        lines.append(b'Content-Disposition: form-data; name="chat_id"')
        lines.append(b'')
        lines.append(str(chat_id).encode())

        safe_caption = caption[:1020]
        lines.append(f"--{boundary}".encode())
        lines.append(b'Content-Disposition: form-data; name="caption"')
        lines.append(b'')
        lines.append(safe_caption.encode("utf-8"))

        lines.append(f"--{boundary}".encode())
        lines.append(b'Content-Disposition: form-data; name="parse_mode"')
        lines.append(b'')
        lines.append(b"HTML")

        lines.append(f"--{boundary}".encode())
        lines.append(f'Content-Disposition: form-data; name="photo"; filename="{symbol}_bb30_chart.png"'.encode())
        lines.append(b"Content-Type: image/png")
        lines.append(b"")
        lines.append(chart_bytes)

        lines.append(f"--{boundary}--".encode())
        lines.append(b"")

        body = b"\r\n".join(lines)
        url = f"https://api.telegram.org/bot{token}/sendPhoto"

        req = urllib.request.Request(url, data=body)
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        req.add_header("Content-Length", str(len(body)))

        ctx = ssl._create_unverified_context()
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
                res = json.loads(resp.read().decode())
                if res.get("ok"):
                    return True
        except Exception as e:
            print(f"[sendPhoto Telegram Error]: {e}. Falling back to sendMessage.")

    # 3. Fallback to sendMessage if photo upload fails
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": caption,
            "parse_mode": "HTML"
        }
        encoded_data = urllib.parse.urlencode(payload).encode("utf-8")
        ctx = ssl._create_unverified_context()
        req2 = urllib.request.Request(url, data=encoded_data)
        with urllib.request.urlopen(req2, context=ctx, timeout=10) as resp:
            return True
    except Exception as e:
        print(f"[sendMessage Fallback Error]: {e}")
        return False
