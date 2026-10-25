import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os

# Set dark theme style
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(15, 8.5), dpi=300)
fig.patch.set_facecolor('#0B0F17')
ax.set_facecolor('#0E131D')

# Grid
ax.grid(color='#1E293B', linestyle='--', linewidth=0.5, alpha=0.5)

# Synthetic realistic candlestick series demonstrating MANAUSDT 4H Short Setup
# Each candle: (open, high, low, close)
candles = [
    # 0 to 4: Uptrend leading to structural high
    (0.0840, 0.0848, 0.0838, 0.0845),
    (0.0845, 0.0855, 0.0843, 0.0852),
    (0.0852, 0.0862, 0.0850, 0.0860),
    (0.0860, 0.0872, 0.0858, 0.0870),
    (0.0870, 0.0880, 0.0868, 0.0875),
    # 5: STEP 1 - INDUCEMENT LIQUIDITY SWEEP (Rejection Wick >= 18%)
    (0.0875, 0.0895, 0.0872, 0.0876), 
    # 6: ORIGIN BEARISH ORDER BLOCK (OB)
    (0.0876, 0.0888, 0.0868, 0.0870),
    # 7 & 8: STEP 2 - AGGRESSIVE DISPLACEMENT (>= 5.0%) & FVG
    (0.0870, 0.0871, 0.0848, 0.0850),
    (0.0850, 0.0852, 0.0835, 0.0838),
    # 9 to 11: PULLBACK RETEST TOWARDS OB
    (0.0838, 0.0848, 0.0836, 0.0846),
    (0.0846, 0.0860, 0.0844, 0.0858),
    (0.0858, 0.0872, 0.0856, 0.0870),
    # 12: STEP 3 - 50% MEAN THRESHOLD (MT) SNIPER ENTRY TAP!
    (0.0870, 0.0879, 0.0866, 0.0868),
    # 13 to 17: STEP 5 - MULTI-STAGE PROFIT SURGE TO TAKE PROFIT
    (0.0868, 0.0870, 0.0855, 0.0856),
    (0.0856, 0.0858, 0.0846, 0.0848),
    (0.0848, 0.0850, 0.0840, 0.0842),
    (0.0842, 0.0844, 0.0836, 0.0838),
    (0.0838, 0.0840, 0.0825, 0.0826),
]

# Draw Candlesticks
for i, (op, hi, lo, cl) in enumerate(candles):
    is_bull = cl >= op
    col = '#00F59B' if is_bull else '#FF4D6A'
    
    # Wick
    ax.plot([i, i], [lo, hi], color=col, linewidth=1.4, zorder=2)
    # Body
    body_bot = min(op, cl)
    body_h = abs(cl - op)
    rect = patches.Rectangle((i - 0.32, body_bot), 0.64, body_h, linewidth=0, facecolor=col, zorder=3)
    ax.add_patch(rect)

# OB High, Low, and 50% Mean Threshold calculation from Bar 6 (Order Block)
ob_high = 0.0888
ob_low = 0.0868
mean_threshold = (ob_high + ob_low) / 2.0  # 0.0878
soft_sl = ob_high + 0.0003                 # 0.0891 (Candle Body Close SL)
take_profit = mean_threshold * (1.0 - 0.03) # 0.085166 (+15% ROE @ 5x)

# 1. Highlight ORDER BLOCK (OB) Zone
ob_rect = patches.Rectangle((5.6, ob_low), 7.0, (ob_high - ob_low), 
                            linewidth=1.2, edgecolor='#A855F7', facecolor='#A855F7', alpha=0.18, zorder=1)
ax.add_patch(ob_rect)
ax.text(5.8, ob_high + 0.0001, "ORIGIN ORDER BLOCK (OB)", color='#C084FC', fontsize=9.5, fontweight='bold')

# 2. Highlight FAIR VALUE GAP (FVG)
fvg_rect = patches.Rectangle((6.8, 0.0852), 4.5, (0.0868 - 0.0852),
                             linewidth=1.0, edgecolor='#38BDF8', facecolor='#38BDF8', alpha=0.12, linestyle=':', zorder=1)
ax.add_patch(fvg_rect)
ax.text(7.0, 0.0858, "FAIR VALUE GAP (FVG Imbalance)", color='#38BDF8', fontsize=8.5, fontweight='bold')

# 3. Mark 50% MEAN THRESHOLD (MT) ENTRY LINE
ax.axhline(mean_threshold, color='#00F59B', linestyle='--', linewidth=2.0, alpha=0.9, zorder=4)
ax.text(0.2, mean_threshold + 0.00012, f"50% MEAN THRESHOLD ENTRY: ${mean_threshold:.4f}", color='#00F59B', fontsize=11, fontweight='black', backgroundcolor='#0B0F17')

# Entry Pointer on Candle 12
ax.annotate("SNIPER ENTRY @ 50% MT\n(Limit Order Filled)", 
            xy=(12, mean_threshold), xytext=(12, mean_threshold + 0.0016),
            arrowprops=dict(facecolor='#00F59B', edgecolor='#00F59B', width=2.5, headwidth=9, shrink=0.08),
            color='#00F59B', fontsize=10.5, fontweight='bold', ha='center',
            bbox=dict(boxstyle="round,pad=0.4", fc="#0B0F17", ec="#00F59B", lw=1.5))

# 4. Mark LIQUIDITY SWEEP (IDM Sweep wick >= 18%) on Candle 5
ax.annotate("STEP 1: LIQUIDITY SWEEP\n(IDM Upper Wick >= 18% Sweep)", 
            xy=(5, 0.0895), xytext=(5, 0.0910),
            arrowprops=dict(facecolor='#F59E0B', edgecolor='#F59E0B', width=2.0, headwidth=8, shrink=0.05),
            color='#F59E0B', fontsize=9.5, fontweight='bold', ha='center',
            bbox=dict(boxstyle="round,pad=0.3", fc="#0B0F17", ec="#F59E0B", lw=1.2))

# 5. Mark DISPLACEMENT >= 5.0% on Candles 7-8
ax.annotate("STEP 2: DISPLACEMENT >= 5.0%\nHeavy Institutional Momentum", 
            xy=(7.5, 0.0845), xytext=(9.2, 0.0825),
            arrowprops=dict(facecolor='#38BDF8', edgecolor='#38BDF8', width=2.0, headwidth=8, shrink=0.05),
            color='#38BDF8', fontsize=9.5, fontweight='bold', ha='center',
            bbox=dict(boxstyle="round,pad=0.3", fc="#0B0F17", ec="#38BDF8", lw=1.2))

# 6. Mark STRUCTURAL SOFT STOP LOSS
ax.axhline(soft_sl, color='#FF4D6A', linestyle='--', linewidth=1.5, alpha=0.8, zorder=4)
ax.text(0.2, soft_sl + 0.0001, f"STRUCTURAL SOFT SL: ${soft_sl:.4f} (Candle Body Close Protection)", color='#FF4D6A', fontsize=10, fontweight='bold', backgroundcolor='#0B0F17')

# 7. Mark STEPPED TRAILING PROFIT ARMOR LADDER
be_price = mean_threshold * (1.0 - 0.01)    # +1.0% drop -> BE lock
trail_price = mean_threshold * (1.0 - 0.02) # +2.0% drop -> Trailing lock
tp_price = mean_threshold * (1.0 - 0.03)    # +3.0% drop -> +15% ROE Full TP

ax.axhline(tp_price, color='#00F59B', linestyle='-', linewidth=2.0, alpha=0.9, zorder=4)
ax.text(12.5, tp_price - 0.00045, f"TAKE PROFIT (TP HIT +15% ROE): ${tp_price:.4f}", color='#00F59B', fontsize=11, fontweight='black',
        bbox=dict(boxstyle="round,pad=0.3", fc="#0B0F17", ec="#00F59B", lw=1.5))

# Stage 1 and Stage 2 Trailing SL Markers
ax.plot([13, 14.5], [be_price, be_price], color='#38BDF8', linewidth=1.5, linestyle=':')
ax.text(14.6, be_price, "Stage 1 Armor: SL to Breakeven (+0.1% Lock)", color='#38BDF8', fontsize=8.5, fontweight='bold')

ax.plot([14.5, 16], [trail_price, trail_price], color='#F59E0B', linewidth=1.5, linestyle=':')
ax.text(16.1, trail_price, "Stage 2 Armor: Lock +5% ROE Trailing", color='#F59E0B', fontsize=8.5, fontweight='bold')

# 4-Sentries Diagnostic Matrix HUD Box (Top Right)
hud_text = (
    "HERMES 3.0 MODEL 2A — 4-SENTRIES HUD\n"
    "------------------------------------\n"
    " [OK] Sentry 1: BTC Macro EMA50 (Safe)\n"
    " [OK] Sentry 2: Displacement >= 5.0% FVG\n"
    " [OK] Sentry 3: IDM Sweep Wick >= 18%\n"
    " [OK] Sentry 4: OB Freshness <= 28 Bars\n"
    "------------------------------------\n"
    " Target: +15.0% ROE | SL: Soft Body Close"
)
ax.text(0.02, 0.28, hud_text, transform=ax.transAxes, color='#E2E8F0', fontsize=8.5,
        fontfamily='monospace', va='top', ha='left',
        bbox=dict(boxstyle="round,pad=0.6", fc="#111827", ec="#38BDF8", lw=1.2, alpha=0.9))

# Chart Title and Subtitle
plt.title("HERMES 3.0 MODEL 2A: INSTITUTIONAL 50% MEAN THRESHOLD ENTRY MODEL\nMANAUSDT 4H — Real Trade Execution Anatomy (Displacement -> 50% MT Tap -> +15% ROE TP)",
          fontsize=13, fontweight='black', color='#FFFFFF', pad=20, ha='center')

# Labels & Limits
ax.set_xlim(-0.8, 18.2)
ax.set_ylim(0.0815, 0.0925)
ax.set_ylabel("Price (USDT)", color='#94A3B8', fontsize=11, fontweight='bold')
ax.set_xlabel("4-Hour Execution Bars Progression &rarr;", color='#94A3B8', fontsize=11, fontweight='bold')

# Formatting ticks
ax.tick_params(colors='#94A3B8', which='both', labelsize=9.5)
for spine in ax.spines.values():
    spine.set_color('#334155')

plt.tight_layout()

# Save image in artifact directory and static directory
artifact_dir = r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c"
out_path_artifact = os.path.join(artifact_dir, "hermes30_entry_model_chart.png")
out_path_static = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\static\hermes30_entry_model_chart.png"

plt.savefig(out_path_artifact, dpi=300, bbox_inches='tight')
plt.savefig(out_path_static, dpi=300, bbox_inches='tight')
plt.close()

print(f"Chart saved successfully at:")
print(f"  Artifact: {out_path_artifact}")
print(f"  Static: {out_path_static}")
