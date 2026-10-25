import os
import sys
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

OUT_DIR = r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c"
OUT_PATH = os.path.join(OUT_DIR, "bb10_strategy_visual_guide.png")

# High-resolution: 2000 x 1200
W, H = 2000, 1200
img = Image.new("RGB", (W, H), color="#080c14")
draw = ImageDraw.Draw(img)

# Load fonts
try:
    font_hero = ImageFont.truetype("arialbd.ttf", 38)
    font_title = ImageFont.truetype("arialbd.ttf", 26)
    font_bold = ImageFont.truetype("arialbd.ttf", 20)
    font_med = ImageFont.truetype("arial.ttf", 18)
    font_small = ImageFont.truetype("arial.ttf", 15)
    font_badge = ImageFont.truetype("arialbd.ttf", 16)
    font_step_num = ImageFont.truetype("arialbd.ttf", 28)
except:
    font_hero = font_title = font_bold = font_med = font_small = font_badge = font_step_num = ImageFont.load_default()

# -------------------------------------------------------------
# 1. HEADER SECTION
# -------------------------------------------------------------
draw.rectangle([(0, 0), (W, 110)], fill="#0f172a")
draw.line([(0, 110), (W, 110)], fill="#334155", width=2)

draw.text((50, 20), "👑 BB 1.0 (BOOMING BULLS) LIQUIDITY SNIPER — SETUP ANATOMY", fill="#38bdf8", font=font_hero)
draw.text((50, 70), "MODEL 3: PDL SWEEP ➔ EXTREME ORDER BLOCK ➔ 50% MT RETEST ➔ STEPPED TRAILING SL", fill="#94a3b8", font=font_med)

# Header Badge
draw.rounded_rectangle([(W - 420, 25), (W - 50, 85)], radius=10, fill="#064e3b", outline="#10b981", width=2)
draw.text((W - 395, 35), "MODEL 3 SELECTED", fill="#34d399", font=font_bold)
draw.text((W - 395, 58), "52% Pure Win | 61% Green Rate", fill="#a7f3d0", font=font_small)

# -------------------------------------------------------------
# 2. MAIN CHART AREA (Y: 130 to 860)
# -------------------------------------------------------------
CHART_L, CHART_R = 60, W - 60
CHART_T, CHART_B = 130, 850

# Subtle Chart Background & Grid
draw.rectangle([(CHART_L, CHART_T), (CHART_R, CHART_B)], fill="#0b1120", outline="#1e293b", width=2)

for y_grid in range(CHART_T + 60, CHART_B, 70):
    draw.line([(CHART_L, y_grid), (CHART_R, y_grid)], fill="#111c30", width=1)
for x_grid in range(CHART_L + 120, CHART_R, 120):
    draw.line([(x_grid, CHART_T), (x_grid, CHART_B)], fill="#111c30", width=1)

# Price mapping function
P_MIN = 94.0
P_MAX = 104.0
def p2y(price):
    return int(CHART_B - (price - P_MIN) / (P_MAX - P_MIN) * (CHART_B - CHART_T - 40) - 20)

# KEY HORIZONTAL LINES
PDL = 97.00
ENTRY = 96.50
SL = 95.05
TP1 = 97.95
TP2 = 98.68
TP3 = 99.40
TP_FINAL = 101.50

y_pdl = p2y(PDL)
y_entry = p2y(ENTRY)
y_sl = p2y(SL)
y_tp1 = p2y(TP1)
y_tp2 = p2y(TP2)
y_tp3 = p2y(TP3)
y_tp_final = p2y(TP_FINAL)

# 1. PDL Support Line (Cyan Bold)
draw.line([(CHART_L, y_pdl), (CHART_R - 220, y_pdl)], fill="#0284c7", width=3)
draw.rounded_rectangle([(CHART_R - 210, y_pdl - 16), (CHART_R - 10, y_pdl + 16)], radius=6, fill="#0369a1")
draw.text((CHART_R - 200, y_pdl - 10), "PDL SUPPORT: $97.00", fill="#ffffff", font=font_badge)

# 2. Stop Loss Line (Red Bold)
draw.line([(CHART_L + 250, y_sl), (CHART_R - 220, y_sl)], fill="#ef4444", width=3)
draw.rounded_rectangle([(CHART_R - 210, y_sl - 16), (CHART_R - 10, y_sl + 16)], radius=6, fill="#b91c1c")
draw.text((CHART_R - 200, y_sl - 10), "STOP LOSS: $95.05", fill="#ffffff", font=font_badge)

# 3. Entry Line (Bright Green Bold)
draw.line([(CHART_L + 350, y_entry), (CHART_R - 220, y_entry)], fill="#10b981", width=3)
draw.rounded_rectangle([(CHART_R - 210, y_entry - 16), (CHART_R - 10, y_entry + 16)], radius=6, fill="#047857")
draw.text((CHART_R - 200, y_entry - 10), "ENTRY 50% MT: $96.50", fill="#ffffff", font=font_badge)

# 4. Profit Target / Trailing Milestones
draw.line([(CHART_L + 650, y_tp1), (CHART_R - 220, y_tp1)], fill="#38bdf8", width=1)
draw.text((CHART_R - 200, y_tp1 - 10), "+1.0R ($97.95) ➔ SL to BE", fill="#38bdf8", font=font_small)

draw.line([(CHART_L + 750, y_tp2), (CHART_R - 220, y_tp2)], fill="#34d399", width=1)
draw.text((CHART_R - 200, y_tp2 - 10), "+1.5R ($98.68) ➔ Lock +1R", fill="#34d399", font=font_small)

draw.line([(CHART_L + 850, y_tp3), (CHART_R - 220, y_tp3)], fill="#fbbf24", width=1)
draw.text((CHART_R - 200, y_tp3 - 10), "+2.0R ($99.40) ➔ Lock +1.5R", fill="#fbbf24", font=font_small)

draw.line([(CHART_L + 950, y_tp_final), (CHART_R - 220, y_tp_final)], fill="#f59e0b", width=2)
draw.rounded_rectangle([(CHART_R - 210, y_tp_final - 16), (CHART_R - 10, y_tp_final + 16)], radius=6, fill="#d97706")
draw.text((CHART_R - 200, y_tp_final - 10), "TARGET HIT (+3R+)", fill="#ffffff", font=font_badge)

# -------------------------------------------------------------
# 3. CANDLESTICK DATA & PLOTTING
# -------------------------------------------------------------
candles = [
    # Fall down to PDL
    (140, 100.8, 101.2, 99.8, 100.0),
    (200, 100.0, 100.3, 98.7, 98.9),
    (260, 98.9, 99.1, 97.4, 97.6),
    (320, 97.6, 97.9, 96.9, 97.2),
    
    # [CANDLE 5: THE LIQUIDITY SWEEP] - Pierces PDL (97.00), drops to 95.20, closes at 97.50!
    (400, 97.2, 97.8, 95.2, 97.5),
    
    # [CANDLE 6 & 7: DISPLACEMENT PUMP + FVG CREATION]
    (470, 97.5, 99.5, 97.3, 99.4),
    (540, 99.4, 100.6, 99.2, 100.3),
    
    # [CANDLE 8, 9, 10: PULLBACK TO 50% MT LEVEL FOR LIMIT ENTRY]
    (610, 100.3, 100.5, 99.0, 99.2),
    (680, 99.2, 99.4, 97.8, 98.0),
    (750, 98.0, 98.2, 96.5, 97.6), # <--- [ENTRY TRIGGERED AT 96.50!]
    
    # [CANDLE 11-16: TREND EXPLOSION WITH STEPPED TRAILING]
    (820, 97.6, 99.0, 97.4, 98.8),
    (890, 98.8, 100.0, 98.6, 99.8),
    (960, 99.8, 101.0, 99.6, 100.8),
    (1030, 100.8, 101.8, 100.6, 101.6),
    (1100, 101.6, 102.5, 101.4, 102.3),
    (1170, 102.3, 103.2, 102.1, 103.0),
]

# Shaded Order Block Area (Purple Box)
ob_x1 = 370
ob_x2 = 750
ob_y_top = p2y(97.8)
ob_y_bot = p2y(95.2)
draw.rectangle([(ob_x1, ob_y_top), (ob_x2, ob_y_bot)], fill="#1e1b4b", outline="#6366f1", width=2)
draw.text((ob_x1 + 15, ob_y_bot - 30), "EXTREME ORIGIN ORDER BLOCK", fill="#a5b4fc", font=font_badge)

# Shaded FVG (Imbalance) Area
fvg_y_top = p2y(99.2)
fvg_y_bot = p2y(97.8)
draw.rectangle([(440, fvg_y_top), (680, fvg_y_bot)], fill="#172554", outline="#3b82f6", width=1)
draw.text((450, fvg_y_top + 10), "FAIR VALUE GAP (FVG)", fill="#93c5fd", font=font_small)

# Draw Candles
C_W = 32
for x, c_o, c_h, c_l, c_c in candles:
    y_o = p2y(c_o)
    y_h = p2y(c_h)
    y_l = p2y(c_l)
    y_c = p2y(c_c)
    
    is_bull = c_c >= c_o
    body_color = "#00e676" if is_bull else "#ff1744"
    wick_color = "#69f0ae" if is_bull else "#ff5252"
    
    # Wick
    draw.line([(x, y_h), (x, y_l)], fill=wick_color, width=4)
    # Body
    b_top = min(y_o, y_c)
    b_bot = max(y_o, y_c)
    if b_bot == b_top:
        b_bot += 3
    draw.rectangle([(x - C_W//2, b_top), (x + C_W//2, b_bot)], fill=body_color, outline=body_color)

# -------------------------------------------------------------
# 4. VISUAL ANNOTATIONS WITH BOLD NUMBERED BADGES
# -------------------------------------------------------------

# STEP 1: LIQUIDITY SWEEP WICK
sweep_x = 400
sweep_wick_y = p2y(95.2)
draw.ellipse([(sweep_x - 30, sweep_wick_y - 30), (sweep_x + 30, sweep_wick_y + 30)], outline="#fbbf24", width=3)
# Badge 1
draw.rounded_rectangle([(sweep_x - 170, sweep_wick_y + 40), (sweep_x + 70, sweep_wick_y + 115)], radius=8, fill="#451a03", outline="#f59e0b", width=2)
draw.text((sweep_x - 155, sweep_wick_y + 48), "❶ STEP 1: LIQUIDITY SWEEP", fill="#fbbf24", font=font_bold)
draw.text((sweep_x - 155, sweep_wick_y + 75), "PDL sweep kar ke 78% wick chhod kar", fill="#fde68a", font=font_small)
draw.text((sweep_x - 155, sweep_wick_y + 93), "wapis level ke upar close hui (TRAP!)", fill="#ffffff", font=font_small)
draw.line([(sweep_x, sweep_wick_y + 30), (sweep_x, sweep_wick_y + 40)], fill="#f59e0b", width=2)

# STEP 2: DISPLACEMENT PUMP
pump_x = 540
pump_y = p2y(100.3)
draw.rounded_rectangle([(pump_x - 50, pump_y - 95), (pump_x + 190, pump_y - 20)], radius=8, fill="#1e1b4b", outline="#818cf8", width=2)
draw.text((pump_x - 35, pump_y - 88), "❷ STEP 2: DISPLACEMENT", fill="#c7d2fe", font=font_bold)
draw.text((pump_x - 35, pump_y - 62), "Big green candle ne FVG banaya", fill="#e0e7ff", font=font_small)
draw.text((pump_x - 35, pump_y - 42), "Origin candle = Extreme OB", fill="#818cf8", font=font_small)
draw.line([(pump_x, pump_y - 20), (pump_x, pump_y)], fill="#818cf8", width=2)

# STEP 3: 50% MT LIMIT ENTRY
entry_x = 750
entry_y = p2y(96.50)
draw.ellipse([(entry_x - 25, entry_y - 25), (entry_x + 25, entry_y + 25)], outline="#10b981", width=3)
draw.rounded_rectangle([(entry_x - 80, entry_y - 105), (entry_x + 180, entry_y - 30)], radius=8, fill="#064e3b", outline="#34d399", width=2)
draw.text((entry_x - 65, entry_y - 98), "❸ STEP 3: LIMIT ENTRY", fill="#34d399", font=font_bold)
draw.text((entry_x - 65, entry_y - 72), "Price ne 50% MT ($96.50) tap kiya", fill="#a7f3d0", font=font_small)
draw.text((entry_x - 65, entry_y - 52), "Order automatically FILL hua!", fill="#ffffff", font=font_small)
draw.line([(entry_x, entry_y - 30), (entry_x, entry_y - 10)], fill="#34d399", width=2)

# STEP 4: STOP LOSS PLACEMENT
sl_callout_x = 420
draw.rounded_rectangle([(sl_callout_x - 120, y_sl - 75), (sl_callout_x + 150, y_sl - 10)], radius=8, fill="#450a0a", outline="#ef4444", width=2)
draw.text((sl_callout_x - 105, y_sl - 68), "❹ STEP 4: PROTECTED SL", fill="#f87171", font=font_bold)
draw.text((sl_callout_x - 105, y_sl - 44), "Wick low ke piche 0.15% buffer", fill="#fecaca", font=font_small)
draw.text((sl_callout_x - 105, y_sl - 26), "SL = $95.05 (Risk bohot chhota)", fill="#ffffff", font=font_small)

# STEP 5: STEPPED TRAILING SL LADDER
trail_x = 1000
draw.rounded_rectangle([(trail_x - 40, p2y(101.5) - 100), (trail_x + 240, p2y(101.5) - 15)], radius=8, fill="#0f172a", outline="#38bdf8", width=2)
draw.text((trail_x - 25, p2y(101.5) - 92), "❺ STEP 5: STEPPED TRAILING", fill="#38bdf8", font=font_bold)
draw.text((trail_x - 25, p2y(101.5) - 68), "• +1.0R hit ➔ SL moved to +0.2R (BE)", fill="#e2e8f0", font=font_small)
draw.text((trail_x - 25, p2y(101.5) - 48), "• +1.5R hit ➔ SL locked at +1.0R", fill="#34d399", font=font_small)
draw.text((trail_x - 25, p2y(101.5) - 28), "• Runner waves continue to +3.0R!", fill="#fbbf24", font=font_small)

# -------------------------------------------------------------
# 5. BOTTOM 5-CARD INFOGRAPHIC BAR (Y: 880 to 1180)
# -------------------------------------------------------------
draw.rectangle([(0, 880), (W, H)], fill="#0b0f19")
draw.line([(0, 880), (W, 880)], fill="#1e293b", width=2)

cards = [
    {
        "num": "1",
        "title": "LIQUIDITY SWEEP",
        "tag": "Entry Signal",
        "color": "#f59e0b",
        "bg": "#1c1917",
        "lines": [
            "Previous Day Low ($97.00) ko todkar",
            "market neeche jati hai lekin sustain",
            "nahi karti. Badi lower wick (>=25%)",
            "chhodkar upar aati hai. (Fakeout Trap)"
        ]
    },
    {
        "num": "2",
        "title": "EXTREME ORDER BLOCK",
        "tag": "Zone Mark",
        "color": "#818cf8",
        "bg": "#1e1b4b",
        "lines": [
            "Sweep candle ke baad institutional",
            "buyers explosive green candle banate",
            "hain (+1.5% to +2.0% displacement).",
            "FVG banta hai aur base OB ban jata hai."
        ]
    },
    {
        "num": "3",
        "title": "50% MT LIMIT ENTRY",
        "tag": "Execution",
        "color": "#10b981",
        "bg": "#064e3b",
        "lines": [
            "Direct buy nahi karte! Pullback ka wait",
            "karte hain. Jaise hi price OB ke 50%",
            "midpoint ($96.50) par aati hai,",
            "Limit order se sniper entry hoti hai."
        ]
    },
    {
        "num": "4",
        "title": "SAFE STOP LOSS",
        "tag": "Risk Management",
        "color": "#ef4444",
        "bg": "#450a0a",
        "lines": [
            "Stop Loss candle ke low par nahi hota,",
            "balki 0.15% anti-hunt buffer ke sath",
            "$95.05 par rakha jata hai.",
            "Wick hunt se bachat hoti hai."
        ]
    },
    {
        "num": "5",
        "title": "MODEL 3 TRAILING SL",
        "tag": "Profit Locking",
        "color": "#38bdf8",
        "bg": "#0c4a6e",
        "lines": [
            "+1.0R profit par SL Breakeven (+0.2R).",
            "+1.5R par +1.0R profit pakka lock.",
            "+2.0R par +1.5R lock. Market wapis",
            "bhi ghume toh ZERO loss, full profit!"
        ]
    }
]

card_w = (W - 120) // 5
card_h = 270
y_card = 905

for idx, c in enumerate(cards):
    x_c = 50 + idx * (card_w + 5)
    # Card Border & Fill
    draw.rounded_rectangle([(x_c, y_card), (x_c + card_w - 5, y_card + card_h)], radius=12, fill=c["bg"], outline=c["color"], width=2)
    
    # Step Number Pill
    draw.rounded_rectangle([(x_c + 15, y_card + 15), (x_c + 50, y_card + 50)], radius=6, fill=c["color"])
    draw.text((x_c + 24, y_card + 18), c["num"], fill="#000000", font=font_title)
    
    # Tag
    draw.text((x_c + 60, y_card + 15), c["tag"].upper(), fill=c["color"], font=font_badge)
    # Title
    draw.text((x_c + 60, y_card + 32), c["title"], fill="#ffffff", font=font_bold)
    
    draw.line([(x_c + 15, y_card + 65), (x_c + card_w - 20, y_card + 65)], fill="#334155", width=1)
    
    # Text lines
    y_text = y_card + 80
    for l in c["lines"]:
        draw.text((x_c + 15, y_text), l, fill="#e2e8f0", font=font_small)
        y_text += 26

# Save
img.save(OUT_PATH, quality=95)
print(f"Enhanced Visual Guide successfully created: {OUT_PATH}")
