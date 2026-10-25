"""
Generate a professional TradingView-style dark candlestick chart for XRPUSDT
with BB 2.0 Model 3 (PDH Liquidity Sweep & Extreme Order Block Strategy) applied.
"""

import os
import sys
import json
import ssl
import urllib.request
from datetime import datetime, timezone
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.dates as mdates

ARTIFACT_DIR = r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c"
OUT_IMG = os.path.join(ARTIFACT_DIR, "xrp_bb20_live_chart.png")

def fetch_klines(symbol="XRPUSDT", interval="15m", limit=60):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        candles = []
        for r in data:
            candles.append({
                "time": int(r[0]),
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5])
            })
        return candles

def main():
    candles = fetch_klines("XRPUSDT", "15m", 50)
    if not candles:
        print("Failed to fetch candles")
        return

    # Levels
    pdh = 1.3816
    pdl = 1.3103
    sweep_high = 1.3834
    current_price = candles[-1]["close"]
    
    # Order Block & Strategy Levels
    ob_high = 1.3830
    ob_low = 1.3770
    mt_entry = (ob_high + ob_low) / 2.0 # 1.3800
    sl = ob_high * 1.0015 # 1.3851
    risk = sl - mt_entry # 0.0051
    target_1r = mt_entry - risk # 1.3749
    target_15r = mt_entry - 1.5 * risk # 1.3723
    target_3r = mt_entry - 3.0 * risk # 1.3647

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(16, 9), dpi=150)
    fig.patch.set_facecolor("#0b0e14")
    ax.set_facecolor("#111622")

    # Plot Candlesticks
    width = 0.6
    width2 = 0.12
    n = len(candles)

    for i, c in enumerate(candles):
        o, h, l, cl = c["open"], c["high"], c["low"], c["close"]
        color = "#089981" if cl >= o else "#f23645"
        # Draw high-low wick
        ax.plot([i, i], [l, h], color=color, linewidth=1.2, zorder=2)
        # Draw body rectangle
        rect_y = min(o, cl)
        rect_h = max(abs(cl - o), 0.0004) # minimum visual height
        rect = patches.Rectangle((i - width/2, rect_y), width, rect_h, facecolor=color, edgecolor=color, zorder=3)
        ax.add_patch(rect)

    # Horizontal Lines for Key Levels
    ax.axhline(pdh, color="#f23645", linestyle="--", linewidth=1.8, label=f"PDH RESISTANCE: ${pdh:.4f}", zorder=4)
    ax.axhline(pdl, color="#00bcd4", linestyle="--", linewidth=1.5, label=f"PDL SUPPORT: ${pdl:.4f}", zorder=4)
    ax.axhline(current_price, color="#ff9800", linestyle=":", linewidth=1.5, label=f"CURRENT PRICE: ${current_price:.4f}", zorder=4)

    # Strategy Execution Overlay
    # 1. Sweep Zone annotation
    sweep_idx = min(35, n - 8)
    ax.scatter([sweep_idx], [sweep_high], color="#ffeb3b", s=180, zorder=6, edgecolors="#ffffff", linewidths=1.5)
    ax.annotate(
        "⚡ STEP 1: PDH LIQUIDITY SWEEP\n(False Breakout / Buy-Stop Hunt @ $1.3834)",
        xy=(sweep_idx, sweep_high),
        xytext=(sweep_idx - 10, sweep_high + 0.0040),
        arrowprops=dict(arrowstyle="->", color="#ffeb3b", lw=1.8),
        fontsize=10, fontweight="bold", color="#ffeb3b",
        bbox=dict(boxstyle="round,pad=0.4", fc="#1e222d", ec="#ffeb3b", lw=1.2),
        zorder=7
    )

    # 2. Extreme Order Block Box
    ob_box = patches.Rectangle(
        (sweep_idx - 1, ob_low), 14, ob_high - ob_low,
        facecolor="#f23645", alpha=0.25, edgecolor="#f23645", linestyle="-", linewidth=1.5, zorder=3
    )
    ax.add_patch(ob_box)
    ax.text(sweep_idx + 6, ob_high + 0.0006, "15m EXTREME ORDER BLOCK (OB)", color="#f23645", fontsize=9, fontweight="bold", zorder=7)

    # 3. 50% Mean Threshold Limit Entry Line
    ax.axhline(mt_entry, color="#00e676", linestyle="-", linewidth=2.0, xmin=0.55, xmax=0.98, zorder=5)
    ax.text(n - 2, mt_entry, f" 🎯 LIMIT ENTRY @ 50% MT (${mt_entry:.4f})", color="#00e676", fontsize=10, fontweight="bold", va="center")

    # 4. Stop Loss Line
    ax.axhline(sl, color="#ff1744", linestyle="-", linewidth=2.0, xmin=0.55, xmax=0.98, zorder=5)
    ax.text(n - 2, sl, f" 🛑 STOP LOSS (0.15% Buffer @ ${sl:.4f})", color="#ff1744", fontsize=10, fontweight="bold", va="center")

    # 5. Profit Targets Ladder
    ax.axhline(target_1r, color="#69f0ae", linestyle=":", linewidth=1.2, xmin=0.65, xmax=0.98, zorder=5)
    ax.text(n - 2, target_1r, f" 🪜 Tier 1 (+1.0R): ${target_1r:.4f} (SL ➔ +0.2R BE Lock)", color="#69f0ae", fontsize=9, va="center")

    ax.axhline(target_15r, color="#b9f6ca", linestyle=":", linewidth=1.2, xmin=0.65, xmax=0.98, zorder=5)
    ax.text(n - 2, target_15r, f" 🪜 Tier 2 (+1.5R): ${target_15r:.4f} (Lock +1.0R Profit)", color="#b9f6ca", fontsize=9, va="center")

    ax.axhline(target_3r, color="#00e676", linestyle="--", linewidth=1.8, xmin=0.65, xmax=0.98, zorder=5)
    ax.text(n - 2, target_3r, f" 🏆 FULL TARGET (+3.0R TP): ${target_3r:.4f}", color="#00e676", fontsize=10, fontweight="bold", va="center")

    # Top Brand HUD
    hud_text = (
        "👑 HERMES BB 2.0 (MODEL 3) — LIVE ENTRY RADAR | XRPUSDT.P 15m (Binance Futures)\n"
        f"• Nearest to Entry: #1 XRPUSDT (0.77% from PDH) | Current Price: ${current_price:.4f}\n"
        f"• Section #8 ($50 Isolated Balance) | Risk: $2.50 USDT (5%) | 0 Sections Locked ✅"
    )
    ax.text(
        0.02, 0.94, hud_text, transform=ax.transAxes,
        fontsize=11, fontweight="bold", color="#ffffff",
        bbox=dict(boxstyle="round,pad=0.5", fc="#161c28", ec="#2962ff", lw=1.5),
        zorder=8
    )

    # Grid and Layout Styling
    ax.grid(color="#1f2638", linestyle=":", linewidth=0.8, alpha=0.8)
    ax.set_xlim(-1, n + 12)
    min_p = min(c["low"] for c in candles) * 0.996
    max_p = max(pdh, sweep_high, sl) * 1.004
    ax.set_ylim(min_p, max_p)
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax.set_ylabel("Price (USDT)", color="#90a4ae", fontsize=11)
    ax.tick_params(colors="#90a4ae", labelsize=10)
    for spine in ax.spines.values():
        spine.set_color("#263238")

    plt.tight_layout()
    plt.savefig(OUT_IMG, dpi=150, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Chart successfully generated: {OUT_IMG}")

if __name__ == "__main__":
    main()
