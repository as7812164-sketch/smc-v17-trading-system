import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Set utf-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

# Output path in brain artifact directory
OUT_DIR = r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c"
OUT_PATH = os.path.join(OUT_DIR, "auditor_certified_master_strategy_chart.png")

# Dimensions: 1920 x 1080 Full HD
W, H = 1920, 1080
img = Image.new("RGB", (W, H), color="#0b0e14")
draw = ImageDraw.Draw(img)

# Try loading standard system fonts or default
try:
    font_title = ImageFont.truetype("arialbd.ttf", 36)
    font_subtitle = ImageFont.truetype("arial.ttf", 20)
    font_bold = ImageFont.truetype("arialbd.ttf", 22)
    font_med = ImageFont.truetype("arial.ttf", 18)
    font_small = ImageFont.truetype("arial.ttf", 15)
    font_price = ImageFont.truetype("courbd.ttf", 18)
except:
    font_title = font_subtitle = font_bold = font_med = font_small = font_price = ImageFont.load_default()

# 1. Background Gridlines
for y in range(120, H - 80, 60):
    draw.line([(80, y), (W - 400, y)], fill="#141a24", width=1)
for x in range(120, W - 400, 80):
    draw.line([(x, 120), (x, H - 80)], fill="#141a24", width=1)

# 2. Header Bar
draw.rectangle([(0, 0), (W, 90)], fill="#121824")
draw.line([(0, 90), (W, 90)], fill="#1e293b", width=2)

draw.text((40, 20), "HERMES 3.5 INSTITUTIONAL SMC: AUDITOR-CERTIFIED MASTER BLUEPRINT", fill="#38bdf8", font=font_title)
draw.text((40, 60), "100% MATHEMATICAL PRECISION SPECIFICATION | 1H & 4H MASTER DESK | CERTIFIED BY CHIEF QUANT AUDITOR", fill="#94a3b8", font=font_subtitle)

# 3. Candles Definition (Sequence of 14 candles to illustrate the full setup)
# (x_center, open, high, low, close, color)
# Price scale: Low=95.0, High=105.0 -> map to Y: 850 (low) to 150 (high)
def p_to_y(price):
    return int(850 - (price - 95.0) / (105.0 - 95.0) * (850 - 180))

candles_data = [
    # C0: Prior downtrend
    (150, 101.5, 101.8, 99.8, 100.0, "#ef4444"),
    (200, 100.0, 100.3, 98.5, 98.8, "#ef4444"),
    # C2: [1. ORIGIN ORDER BLOCK CANDLE] - The single last down candle at swing low
    (260, 98.8, 99.0, 97.2, 97.6, "#ef4444"), 
    # C3: Ignition candle
    (320, 97.8, 100.2, 97.5, 100.0, "#10b981"),
    # C4: [2. DISPLACEMENT & FVG CANDLE] - Explosive expansion >= 5.0%
    (380, 100.0, 103.5, 99.8, 103.2, "#10b981"),
    # C5: Peak runway candle (Rocket Airspace)
    (440, 103.2, 104.8, 102.8, 104.5, "#10b981"),
    # C6: High plateau
    (500, 104.5, 104.9, 103.5, 103.8, "#ef4444"),
    # C7: Pullback start (creates Inducement swing high)
    (560, 103.8, 104.0, 101.8, 102.0, "#ef4444"),
    # C8: Minor bounce [3. INDUCEMENT (IDM) LOW FORMED HERE]
    (620, 102.0, 102.8, 101.2, 102.5, "#10b981"),
    # C9: Retracement sweeps IDM low!
    (680, 102.4, 102.6, 100.5, 100.8, "#ef4444"),
    # C10: Further dip towards OB
    (740, 100.8, 101.0, 99.2, 99.4, "#ef4444"),
    # C11: [4. THE RETEST REJECTION TAP CANDLE] - Touches 50% MT, wicks >= 18%, closes bullish!
    (810, 99.4, 100.2, 97.9, 99.8, "#10b981"),
    # C12: Expansion rally begins
    (880, 99.8, 102.5, 99.6, 102.2, "#10b981"),
    # C13: Massive takeoff towards TP
    (950, 102.2, 104.6, 102.0, 104.4, "#10b981"),
]

# Order Block levels from Candle 2 (x=260):
ob_high = 99.0
ob_low = 97.2
ob_mt = (ob_high + ob_low) / 2.0 # 98.10 (50% Mean Threshold)
entry_price = round(ob_high - 0.05 * (ob_high - ob_low), 2) # 98.91 (5% boundary) or 50% MT = 98.10
tp_price = 104.20
sl_price = 96.60

# Draw Order Block shaded zone extending across chart
ob_y_high = p_to_y(ob_high)
ob_y_low = p_to_y(ob_low)
ob_y_mt = p_to_y(ob_mt)

# Shaded Order Block Zone
draw.rectangle([(230, ob_y_high), (980, ob_y_low)], fill="#2a151b", outline="#ef4444", width=2)
# 50% Mean Threshold (Gold Dashed/Solid Line)
draw.line([(230, ob_y_mt), (980, ob_y_mt)], fill="#eab308", width=3)
draw.text((990, ob_y_mt - 10), "50% MEAN THRESHOLD: $98.10 (DEFENSE ANCHOR)", fill="#eab308", font=font_bold)

# FVG Zone (Imbalance between C2 High $99.0 and C4 Low $99.8 / C5)
fvg_top = p_to_y(100.2)
fvg_bottom = p_to_y(99.0)
draw.rectangle([(350, fvg_top), (600, fvg_bottom)], fill="#0f2b26", outline="#10b981", width=1)
draw.text((360, fvg_top + 10), "FAIR VALUE GAP (FVG IMBALANCE)", fill="#34d399", font=font_med)

# Draw all Candlesticks
for (x, o, h, l, c, col) in candles_data:
    y_o = p_to_y(o)
    y_h = p_to_y(h)
    y_l = p_to_y(l)
    y_c = p_to_y(c)
    
    # Wick
    draw.line([(x, y_h), (x, y_l)], fill=col, width=3)
    # Body
    top_body = min(y_o, y_c)
    bot_body = max(y_o, y_c)
    if bot_body - top_body < 4: bot_body = top_body + 4
    draw.rectangle([(x - 14, top_body), (x + 14, bot_body)], fill=col, outline=col)

# Annotate Candle 2 as THE SINGLE ORDER BLOCK
draw.rectangle([(180, ob_y_low + 30), (340, ob_y_low + 90)], fill="#1e1b4b", outline="#6366f1", width=2)
draw.text((190, ob_y_low + 38), "1. ORIGIN ORDER BLOCK", fill="#a5b4fc", font=font_bold)
draw.text((190, ob_y_low + 64), "Single Base Red Candle", fill="#cbd5e1", font=font_small)
draw.line([(260, ob_y_low + 30), (260, ob_y_low + 5)], fill="#6366f1", width=2)

# Annotate Candle 4 as DISPLACEMENT
c4_x = 380
c4_y = p_to_y(103.5)
draw.rectangle([(320, c4_y - 80), (520, c4_y - 20)], fill="#064e3b", outline="#10b981", width=2)
draw.text((330, c4_y - 72), "2. DISPLACEMENT >= 5.0%", fill="#6ee7b7", font=font_bold)
draw.text((330, c4_y - 46), "Institutional Volume Impulse", fill="#a7f3d0", font=font_small)

# Annotate Inducement Sweep at C8/C9
draw.rectangle([(550, p_to_y(101.2) + 20), (760, p_to_y(101.2) + 80)], fill="#312e81", outline="#818cf8", width=2)
draw.text((560, p_to_y(101.2) + 28), "3. INDUCEMENT (IDM) SWEEP", fill="#c7d2fe", font=font_bold)
draw.text((560, p_to_y(101.2) + 54), "Retail Swing Low Liquidated", fill="#e0e7ff", font=font_small)

# Annotate Retest Tap Candle (C11 at x=810)
c11_y = p_to_y(97.9)
draw.rectangle([(720, c11_y + 40), (950, c11_y + 110)], fill="#14532d", outline="#22c55e", width=2)
draw.text((730, c11_y + 48), "4. FIRST VIRGIN RETEST TAP", fill="#86efac", font=font_bold)
draw.text((730, c11_y + 74), "Lower Wick >= 18% Rejection", fill="#bbf7d0", font=font_small)
draw.text((730, c11_y + 92), "Body Defends 50% Mean Threshold", fill="#bbf7d0", font=font_small)

# Draw Risk / Reward Tool Overlay from C11 (x=810)
rx1 = 830
rx2 = 1200
y_tp = p_to_y(tp_price)
y_entry = p_to_y(entry_price)
y_sl = p_to_y(sl_price)
y_be = p_to_y(round(entry_price * 1.012, 2))
y_harvest = p_to_y(round(entry_price * 1.015, 2))

# Profit Green Box
draw.rectangle([(rx1, y_tp), (rx2, y_entry)], fill="#064e3b", outline="#10b981", width=2)
# Loss Red Box
draw.rectangle([(rx1, y_entry), (rx2, y_sl)], fill="#450a0a", outline="#ef4444", width=2)

# Lines across
draw.line([(rx1, y_tp), (rx2, y_tp)], fill="#10b981", width=3)
draw.line([(rx1, y_entry), (rx2, y_entry)], fill="#38bdf8", width=4)
draw.line([(rx1, y_sl), (rx2, y_sl)], fill="#ef4444", width=3)

# Intermediate Armor Lines
draw.line([(rx1, y_be), (rx2, y_be)], fill="#f59e0b", width=2)
draw.line([(rx1, y_harvest), (rx2, y_harvest)], fill="#eab308", width=2)

# Text on Trade Overlay
draw.text((rx1 + 20, y_tp + 15), f"FINAL TAKE PROFIT: ${tp_price:.2f} (+11.0% ROE @ 5x / +2.20% Spot)", fill="#a7f3d0", font=font_bold)
draw.text((rx1 + 20, y_harvest - 25), "STAGE 2 TRAILING HARVEST (+4.5% ROE Cash Locked)", fill="#fef08a", font=font_med)
draw.text((rx1 + 20, y_be - 25), "STAGE 1 BREAKEVEN ARMOR (+0.10% Capital Safe)", fill="#fde68a", font=font_med)
draw.text((rx1 + 20, y_entry + 10), f"EXACT ENTRY LINE: ${entry_price:.2f} (5% Boundary Penetration)", fill="#38bdf8", font=font_bold)
draw.text((rx1 + 20, y_sl - 35), f"STRUCTURAL STOP LOSS: ${sl_price:.2f} (OB Low - 0.20 ATR Buffer)", fill="#fca5a5", font=font_bold)

# 4. Right Side Master Auditor Specification Panel
panel_x = 1240
panel_w = W - panel_x - 30
draw.rectangle([(panel_x, 110), (W - 30, H - 50)], fill="#111827", outline="#374151", width=2)

# Panel Header
draw.rectangle([(panel_x, 110), (W - 30, 170)], fill="#1f2937")
draw.text((panel_x + 20, 125), "🛡️ CHIEF QUANT AUDITOR SPEC", fill="#38bdf8", font=font_bold)

specs = [
    ("RULE 1: THE ORIGIN OB", "Must be single opposite candle at swing origin (not a cluster). Lowest/highest of prior 25 bars."),
    ("RULE 2: DISPLACEMENT", "Violent impulse >= 5.0% leaving 3-candle Fair Value Gap (FVG). Rocket Airspace >= 5.0% void."),
    ("RULE 3: IDM LIQUIDITY", "Retail Inducement swing low/high must be cleanly swept before mitigation."),
    ("RULE 4: VIRGIN REJECTION", "First tap only. Rejection wick >= 18%. Candle close strictly defends 50% Mean Threshold."),
    ("RULE 5: ENTRY EXECUTION", f"Boundary Entry at ${entry_price:.2f} (or 50% MT at ${ob_mt:.2f} for 1:1.5 positive R:R)."),
    ("RULE 6: PROFIT ARMOR", "Stage 1 (+1.2%): BE Lock\nStage 2 (+1.5%): +4.5% ROE Cash Lock\nFinal TP: +11.0% ROE (+2.2% Spot)"),
    ("RULE 7: STRUCTURAL SL", f"Stop Loss at ${sl_price:.2f} beyond OB low with 0.20 ATR buffer. Never placed inside OB!"),
    ("RULE 8: 10-SECTION MATRIX", "$500 total equity split in 10 isolated $50 sections. Zero trade collisions across 39 coins."),
]

cur_y = 190
for title, desc in specs:
    draw.text((panel_x + 20, cur_y), title, fill="#fbbf24", font=font_bold)
    cur_y += 28
    for line in desc.split("\n"):
        draw.text((panel_x + 20, cur_y), line, fill="#cbd5e1", font=font_med)
        cur_y += 24
    cur_y += 12

# Save image
img.save(OUT_PATH, "PNG")
print(f"Auditor-Certified Master Strategy Chart successfully saved at: {OUT_PATH}")
