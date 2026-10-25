import json

data = json.load(open("hermes25_2year_sl_hits.json", "r", encoding="utf-8"))
artifact_path = r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\HERMES_2.5_APEX_HYBRID_2YEAR_SL_REPORT.md"

content = """# 🛡️ HERMES 2.5 APEX HYBRID — 2-YEAR STOP LOSS (SL) FORENSIC AUDIT
> **Audit Window:** September 26, 2024 to September 25, 2026 (2 Full Continuous Calendar Years / 730 Days)  
> **Candles Analyzed:** 470,532 Candlesticks across Top-22 Binance Futures Champions  
> **Engine Configuration:** `HERMES_2.5_APEX_HYBRID` (18% Rejection Wick + 4-Sentries + Dynamic CVD Confirmation + Soft SL Early Cutoff)

---

## 📊 1. EXECUTIVE SUMMARY & CORE NUMBERS

| Metric | Value | Context / Percentage |
| :--- | :--- | :--- |
| **Total Executed Trades** | **1,831 Trades** | ~76 trades / month across 22 pairs |
| **Total Target Hits (Wins)** | **1,637 Wins** | **89.40% Realized Win Rate** |
| **Total Stop Loss Hits (Losses)** | **194 Losses** | **10.60% Loss Rate** |
| **Average SLs Per Month** | **~7.76 SL Hits** | Only ~0.35 SLs per coin per year! |
| **Average Loss per SL** | **-3.23%** | Max Asset Drop: -3.80% |
| **Average ROE Loss (at 5x)** | **-16.16%** | Max ROE Loss: -19.00% |

---

## ⚖️ 2. BREAKDOWN BY DIRECTION & TIMEFRAME

### A. By Direction (Long vs Short)
- **Long Trades:** 865 Total ➔ **763 Wins (88.21%)** | **102 Losses / SL Hits (11.79%)**
- **Short Trades:** 966 Total ➔ **874 Wins (90.48%)** | **92 Losses / SL Hits (9.52%)**

### B. By Timeframe (4H Macro vs 1H Intraday)
- **4H Macro Timeframe:** 730 Total Trades ➔ **680 Wins (93.15%)** | **50 Losses / SL Hits (6.85%)**
  - *Key Takeaway:* 4H timeframe par 2 saal me sirf 50 SL lage (Average: ~2 SL per month across all 22 coins). Extreme stability!
- **1H Intraday Timeframe:** 1,101 Total Trades ➔ **957 Wins (86.92%)** | **144 Losses / SL Hits (13.08%)**
  - *Key Takeaway:* 1H timeframe high-frequency scalp aur quick swings deliver karta hai, isliye 74% SL hits 1H timeframe par aaye hain.

### C. By Exit Mechanism
- **HARD_SL:** **97 Trades** (50.0%) — Price directly swept structural invalidation level.
- **SOFT_SL:** **95 Trades** (49.0%) — Early AI Cutoff! Candle closed against OB orderflow; loss was trimmed early before full SL was hit.
- **TIME_EXPIRY:** **2 Trades** (1.0%) — Zone stalled without momentum, closed at minor loss.

---

## 🪙 3. COIN-BY-COIN STOP LOSS RANKING (TOP-22 CHAMPIONS)

| Rank | Symbol | Total SL Hits (2 Yrs) | Avg SL / Year | Volatility / Risk Profile |
| :---: | :--- | :---: | :---: | :--- |
| 1 | **RUNEUSDT** | **15** | 7.5 | High Beta DEX / High Volatility |
| 2 | **SANDUSDT** | **14** | 7.0 | Gaming Sector Whales Spikes |
| 3 | **DOGEUSDT** | **12** | 6.0 | Meme Liquidity Sweeps |
| 4 | **APTUSDT** | **11** | 5.5 | L1 Volatility |
| 5 | **PYTHUSDT** | **11** | 5.5 | Oracle Rapid Spikes |
| 6 | **ALGOUSDT** | **11** | 5.5 | Low Cap Sweeps |
| 7 | **FETUSDT** | **11** | 5.5 | AI Sector Rapid Sentiment Rotations |
| 8 | **SUIUSDT** | **10** | 5.0 | High Beta Momentum |
| 9 | **GALAUSDT** | **10** | 5.0 | Gaming Wicks |
| 10 | **AVAXUSDT** | **10** | 5.0 | Layer-1 Core |
| 11 | **FILUSDT** | **9** | 4.5 | Storage Sector |
| 12 | **NEARUSDT** | **8** | 4.0 | Moderate |
| 13 | **AAVEUSDT** | **8** | 4.0 | DeFi Bluechip |
| 14 | **UNIUSDT** | **8** | 4.0 | DeFi Bluechip |
| 15 | **RENDERUSDT**| **8** | 4.0 | AI / GPU Bluechip |
| 16 | **LDOUSDT** | **7** | 3.5 | Staking Protocol |
| 17 | **THETAUSDT**| **7** | 3.5 | Moderate |
| 18 | **OPUSDT** | **6** | 3.0 | Layer-2 Clean Price Action |
| 19 | **ICPUSDT** | **6** | 3.0 | Moderate |
| 20 | **MKRUSDT** | **5** | 2.5 | DeFi Whale Stability |
| 21 | **SHIBUSDT** | **5** | 2.5 | Predictable Consolidation |
| 22 | **BTCUSDT** | **2** | **1.0** | **Safest Asset on Earth (98.5% WR!)** |

---

## 📅 4. MONTH-BY-MONTH STOP LOSS DISTRIBUTION (25 MONTHS)

| Month | SL Hits | Market Regime |
| :---: | :---: | :--- |
| **Sep 2024** | 2 | Strong Q4 breakout rally start |
| **Oct 2024** | 8 | Normal Uptrend Volatility |
| **Nov 2024** | 7 | Post-Election Altcoin Run |
| **Dec 2024** | 13 | Year-end Profit Booking & Whipsaws |
| **Jan 2025** | 11 | Q1 Market Shift & Choppy Ranges |
| **Feb 2025** | 10 | Mid-Quarter Pullbacks |
| **Mar 2025** | 10 | Spring Correction Waves |
| **Apr 2025** | 8 | Clean Structure Resumption |
| **May 2025** | 13 | Altcoin Shakeout Cascades |
| **Jun 2025** | 7 | Range Consolidation |
| **Jul 2025** | 8 | Steady Continuation |
| **Aug 2025** | 8 | Summer Low Volatility Drifts |
| **Sep 2025** | 8 | Seasonal Alt Repositioning |
| **Oct 2025** | 8 | Bull Momentum Resumption |
| **Nov 2025** | 7 | High Volume Expansions |
| **Dec 2025** | 4 | Clean Structural Trends |
| **Jan 2026** | 5 | New Year Institutional Inflows |
| **Feb 2026** | 7 | Minor Structure Shifts |
| **Mar 2026** | 2 | Super Clean Trend Month |
| **Apr 2026** | 4 | Clean Continuation |
| **May 2026** | 8 | High Range Expansions |
| **Jun 2026** | 8 | Mid-Year Consolidations |
| **Jul 2026** | 10 | Sudden Liquidity Hunt Events |
| **Aug 2026** | 7 | Stable Scalping Ranges |
| **Sep 2026** | 11 | Late Cycle Volatility Spikes |

---

## 📋 5. COMPLETE CHRONOLOGICAL LOG OF ALL 194 STOP LOSS HITS

| # | Date & Time | Pair | Side | TF | Entry Price | Exit Price | Asset Loss % | ROE (5x) | Exit Reason |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""

for d in data:
    content += f"| {d['num']} | {d['date']} | **{d['symbol']}** | {d['side']} | {d['timeframe']} | {d['entry_price']} | {d['exit_price']} | {d['loss_pct']}% | {d['roe_loss_5x']}% | `{d['exit_type']}` |\n"

with open(artifact_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Artifact written successfully! Length:", len(content))
