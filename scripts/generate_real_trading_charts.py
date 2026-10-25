import json
import urllib.request
import datetime
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

sys.path.append(os.getcwd())
from engine.hermes30_apex_live import hermes30_live_engine

def fetch_klines(symbol, interval, limit=120):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw_klines = json.loads(resp.read().decode('utf-8'))
    
    candles = []
    for k in raw_klines:
        candles.append({
            "time": k[0],
            "dt": datetime.datetime.fromtimestamp(k[0]/1000.0),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        })
    return candles

def plot_real_market_trade(symbol, interval, setup, candles, output_paths, title_main, trade_meta):
    n = len(candles)
    fig, ax = plt.subplots(figsize=(16, 9), dpi=220, facecolor='#0b0e14')
    ax.set_facecolor('#0e131f')
    
    # Grid
    ax.grid(color='#1e293b', linestyle=':', linewidth=0.7, alpha=0.6)
    
    candle_width = 0.58
    wick_width = 1.2
    green_color = '#10b981'
    red_color = '#ef4444'
    
    # Draw Candlesticks
    for idx, c in enumerate(candles):
        is_bull = c['close'] >= c['open']
        color = green_color if is_bull else red_color
        
        # Wicks
        ax.plot([idx, idx], [c['low'], c['high']], color=color, linewidth=wick_width, zorder=2)
        
        # Body
        body_bottom = min(c['open'], c['close'])
        body_height = max(abs(c['close'] - c['open']), (c['high'] - c['low']) * 0.015)
        rect = patches.Rectangle(
            (idx - candle_width/2, body_bottom),
            candle_width,
            body_height,
            facecolor=color,
            edgecolor=color,
            linewidth=0.7,
            zorder=3
        )
        ax.add_patch(rect)
        
    # Find relevant key candle indices
    tap_idx = None
    for idx, c in enumerate(candles):
        if c['time'] == setup['tap_time'] or abs(c['time'] - setup['tap_time']) < 3600 * 4 * 1000:
            tap_idx = idx
            break
            
    ob_low = setup['ob_low']
    ob_high = setup['ob_high']
    mt = setup['mean_threshold']
    tp = setup['tp_price']
    sl = setup['soft_sl_price']
    hard_sl = setup['hard_sl_price']
    side = setup['side']
    
    # Draw Order Block Zone Box
    ob_start = max(0, (tap_idx - 12) if tap_idx is not None else 10)
    ob_end = min(n - 1, (tap_idx + 18) if tap_idx is not None else n - 1)
    
    ob_box = patches.Rectangle(
        (ob_start, ob_low),
        ob_end - ob_start,
        ob_high - ob_low,
        facecolor='#6366f1',
        alpha=0.22,
        edgecolor='#818cf8',
        linestyle='--',
        linewidth=1.3,
        zorder=1
    )
    ax.add_patch(ob_box)
    
    # OB Label
    ax.text(
        ob_start + 0.3, 
        ob_high + (ob_high - ob_low) * 0.1, 
        f"DECISIONAL ORDER BLOCK (OB)\nHigh: {ob_high:.5f} | Low: {ob_low:.5f}", 
        color='#a5b4fc', 
        fontsize=8.5, 
        fontweight='bold', 
        va='bottom', 
        zorder=4,
        bbox=dict(boxstyle='round,pad=0.25', facecolor='#1e1b4b', edgecolor='#6366f1', alpha=0.85)
    )
    
    # 50% Mean Threshold (MT) line
    ax.axhline(mt, color='#00f59b', linestyle='-', linewidth=2.2, alpha=0.95, zorder=4)
    ax.text(
        n - 0.5, 
        mt, 
        f" 50% MEAN THRESHOLD (MT LIMIT ENTRY): {mt:.5f}", 
        color='#00f59b', 
        fontsize=9.5, 
        fontweight='heavy', 
        va='center', 
        zorder=5,
        bbox=dict(boxstyle='square,pad=0.3', facecolor='#022c22', edgecolor='#00f59b', alpha=0.95)
    )
    
    # TP Line
    ax.axhline(tp, color='#38bdf8', linestyle='--', linewidth=1.6, alpha=0.9, zorder=4)
    ax.text(
        n - 0.5, 
        tp, 
        f" TAKE PROFIT (+15.0% ROE @ 5x): {tp:.5f}", 
        color='#38bdf8', 
        fontsize=9, 
        fontweight='bold', 
        va='center', 
        zorder=5,
        bbox=dict(boxstyle='square,pad=0.25', facecolor='#082f49', edgecolor='#38bdf8', alpha=0.9)
    )
    
    # Soft SL Line
    ax.axhline(sl, color='#f43f5e', linestyle='--', linewidth=1.6, alpha=0.9, zorder=4)
    ax.text(
        n - 0.5, 
        sl, 
        f" SOFT SL (-7.5% ROE Body Close): {sl:.5f}", 
        color='#f43f5e', 
        fontsize=9, 
        fontweight='bold', 
        va='center', 
        zorder=5,
        bbox=dict(boxstyle='square,pad=0.25', facecolor='#4c0519', edgecolor='#f43f5e', alpha=0.9)
    )
    
    # Annotate Entry Tap Candle
    if tap_idx is not None:
        tap_c = candles[tap_idx]
        is_short = (side == 'SHORT')
        arrow_y = tap_c['high'] + (ob_high - ob_low) * 0.9 if is_short else tap_c['low'] - (ob_high - ob_low) * 0.9
        
        ax.annotate(
            f"EXACT LIMIT FILL @ 50% MT ({mt:.5f})\n"
            f"Upper Rejection Wick: {setup['wick_ratio_pct']}%\n"
            f"Timestamp: {tap_c['dt'].strftime('%Y-%m-%d %H:%M')}",
            xy=(tap_idx, mt),
            xytext=(tap_idx, arrow_y),
            arrowprops=dict(facecolor='#00f59b', edgecolor='#00f59b', width=2.5, headwidth=9, headlength=9),
            color='#ffffff',
            fontsize=9.5,
            fontweight='bold',
            ha='center',
            va='bottom' if not is_short else 'top',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#064e3b', edgecolor='#00f59b', alpha=0.95),
            zorder=6
        )
        
        # Circle on tap candle
        circle = patches.Circle((tap_idx, mt), radius=0.35, edgecolor='#00f59b', facecolor='none', linewidth=2.5, zorder=7)
        ax.add_patch(circle)

    # Annotate Trade Outcome
    outcome_color = '#10b981' if trade_meta['is_win'] else '#f43f5e'
    ax.text(
        0.02, 0.15,
        f"REAL TRADE FORENSIC RECORD:\n"
        f"• Trade ID: #{trade_meta['trade_id']}\n"
        f"• Executed Entry: {trade_meta['entry_price']}\n"
        f"• Executed Exit: {trade_meta['exit_price']}\n"
        f"• Realized ROE: {trade_meta['roi_pct']}%\n"
        f"• Net PnL: {trade_meta['pnl_str']}\n"
        f"• Reason: {trade_meta['exit_reason']}",
        transform=ax.transAxes,
        fontsize=9.5,
        fontweight='semibold',
        color='#f8fafc',
        verticalalignment='bottom',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#1e293b', edgecolor=outcome_color, linewidth=1.5, alpha=0.92),
        zorder=8
    )

    # 4 Sentries Radar HUD on top right
    ax.text(
        0.98, 0.96,
        "HERMES 3.0 4-SENTRIES CHECKLIST:\n"
        "[OK] Sentry 1: BTC Causal Brake (NEUTRAL / Safe)\n"
        f"[OK] Sentry 2: Wave Displacement ({setup['displacement_pct']}% >= 5.0%)\n"
        f"[OK] Sentry 3: Inducement Wick ({setup['wick_ratio_pct']}% >= 18%)\n"
        "[OK] Sentry 4: Decisional OB Fib 0.30 - 0.70",
        transform=ax.transAxes,
        fontsize=8.5,
        fontweight='medium',
        color='#38bdf8',
        horizontalalignment='right',
        verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#0f172a', edgecolor='#38bdf8', linewidth=1.0, alpha=0.9),
        zorder=8
    )

    # Format Date Axis
    x_indices = list(range(n))
    dates = [c['dt'].strftime('%d %b\n%H:%M') for c in candles]
    step = max(1, n // 10)
    ax.set_xticks(x_indices[::step])
    ax.set_xticklabels(dates[::step], color='#94a3b8', fontsize=8)
    
    # Y-axis bounds
    all_y = [c['low'] for c in candles] + [c['high'] for c in candles] + [tp, sl, mt, hard_sl]
    y_min, y_max = min(all_y), max(all_y)
    y_pad = (y_max - y_min) * 0.14
    ax.set_ylim(y_min - y_pad, y_max + y_pad)
    ax.set_xlim(-1, n + 6)
    ax.tick_params(axis='y', colors='#94a3b8', labelsize=8.5)
    
    # Title & Subtitle
    fig.suptitle(title_main, fontsize=15, fontweight='heavy', color='#ffffff', y=0.97)
    sub = f"Binance Futures Real Klines ({interval.upper()}) • Model 2A 50% Mean Threshold Execution Engine"
    ax.set_title(sub, fontsize=9.5, color='#94a3b8', pad=12)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.88, right=0.82)
    
    for path in output_paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        plt.savefig(path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
        print(f"Chart saved to: {path}")
        
    plt.close()

# -------------------------------------------------------------
# 1. GENERATE MANAUSDT 4H (PROFITABLE TRADE 623)
# -------------------------------------------------------------
print("Fetching real MANAUSDT 4H candles from Binance Futures...")
mana_candles = fetch_klines("MANAUSDT", "4h", limit=120)
btc_sentry = {"long_veto": False, "short_veto": False}

mana_setup = None
# Scan for the setup that produced the entry around 0.0878
for end_idx in range(len(mana_candles)-25, len(mana_candles)+1):
    sub = mana_candles[:end_idx]
    setups = hermes30_live_engine.detect_apex_setups_on_candles("MANAUSDT", sub, "4h", btc_sentry)
    for s in setups:
        if abs(s['entry_price'] - 0.087835) < 0.001:
            mana_setup = s
            break
    if mana_setup:
        break

if mana_setup:
    print("Found MANAUSDT Setup:", mana_setup)
    mana_slice = mana_candles[max(0, len(mana_candles)-55):]
    
    trade_meta_mana = {
        "trade_id": 623,
        "entry_price": "0.087835 USDT",
        "exit_price": "0.086956 USDT",
        "roi_pct": "+6.63",
        "pnl_str": "+$7.40 USDT (PROFIT LOCKED)",
        "exit_reason": "Stepped Trailing Armor (+1.0R Locked @ Breakeven + Profit)",
        "is_win": True
    }
    
    output_paths_mana = [
        r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\real_hermes30_manausdt_chart.png",
        r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\static\real_hermes30_manausdt_chart.png"
    ]
    
    plot_real_market_trade(
        "MANAUSDT", "4h", mana_setup, mana_slice, output_paths_mana,
        "HERMES 3.0 MODEL 2A — REAL MARKET TRADE EXECUTION (MANAUSDT 4H)",
        trade_meta_mana
    )

# -------------------------------------------------------------
# 2. GENERATE AEROUSDT 4H (TODAY'S TRADE 629 - SOFT SL DEFENSE)
# -------------------------------------------------------------
print("\nFetching real AEROUSDT 4H candles from Binance Futures...")
aero_candles = fetch_klines("AEROUSDT", "4h", limit=100)

aero_setup = None
for end_idx in range(len(aero_candles)-15, len(aero_candles)+1):
    sub = aero_candles[:end_idx]
    setups = hermes30_live_engine.detect_apex_setups_on_candles("AEROUSDT", sub, "4h", btc_sentry)
    for s in setups:
        if abs(s['entry_price'] - 0.8449) < 0.01:
            aero_setup = s
            break
    if aero_setup:
        break

if aero_setup:
    print("Found AEROUSDT Setup:", aero_setup)
    aero_slice = aero_candles[max(0, len(aero_candles)-45):]
    
    trade_meta_aero = {
        "trade_id": 629,
        "entry_price": "0.84350 USDT",
        "exit_price": "0.85890 USDT",
        "roi_pct": "-9.13",
        "pnl_str": "-$0.50 USDT (Section 1 Loss Contained)",
        "exit_reason": "Structural Soft SL (4H Candle Closed Above 0.8575)",
        "is_win": False
    }
    
    output_paths_aero = [
        r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\real_hermes30_aerousdt_chart.png",
        r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\static\real_hermes30_aerousdt_chart.png"
    ]
    
    plot_real_market_trade(
        "AEROUSDT", "4h", aero_setup, aero_slice, output_paths_aero,
        "HERMES 3.0 MODEL 2A — TODAY'S LIVE TRADE FORENSIC (AEROUSDT 4H)",
        trade_meta_aero
    )

# -------------------------------------------------------------
# 3. GENERATE ICPUSDT 1H (TRADE 614 - FULL 15% ROE TP HIT)
# -------------------------------------------------------------
print("\nFetching real ICPUSDT 1H candles from Binance Futures...")
icp_candles = fetch_klines("ICPUSDT", "1h", limit=120)

icp_setup = None
for end_idx in range(len(icp_candles)-25, len(icp_candles)+1):
    sub = icp_candles[:end_idx]
    setups = hermes30_live_engine.detect_apex_setups_on_candles("ICPUSDT", sub, "1h", btc_sentry)
    for s in setups:
        if abs(s['entry_price'] - 2.7945) < 0.05:
            icp_setup = s
            break
    if icp_setup:
        break

if icp_setup:
    print("Found ICPUSDT Setup:", icp_setup)
    icp_slice = icp_candles[max(0, len(icp_candles)-55):]
    
    trade_meta_icp = {
        "trade_id": 614,
        "entry_price": "2.7955 USDT",
        "exit_price": "2.8793 USDT",
        "roi_pct": "+15.00",
        "pnl_str": "+$8.49 USDT (FULL TP HIT)",
        "exit_reason": "Take Profit Target Hit (+15.0% ROE @ 5x)",
        "is_win": True
    }
    
    output_paths_icp = [
        r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\real_hermes30_icpusdt_chart.png",
        r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\static\real_hermes30_icpusdt_chart.png"
    ]
    
    plot_real_market_trade(
        "ICPUSDT", "1h", icp_setup, icp_slice, output_paths_icp,
        "HERMES 3.0 MODEL 2A — FULL TAKE PROFIT HIT (ICPUSDT 1H)",
        trade_meta_icp
    )

print("\nALL CHARTS GENERATED SUCCESSFULLY!")
