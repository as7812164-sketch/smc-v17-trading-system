# 🏛️ SMC V17 CRYPTO SNIPER: MASTER SYSTEM BLUEPRINT
**Version**: 17.0.0-PRO  
**Mission**: Compounding \$50.00 USDT ➔ \$1,000.00 USDT  
**Market**: Crypto Perpetual Futures (Binance & Bitget)  
**Leverage**: 5x Isolated (Strictly Fixed)  
**Execution Mode**: Semi-Automated / First-Tap Outer Boundary Sniper  
**Last Updated**: 23 September 2026

---

## 1. Executive Summary & Core Philosophy

The **SMC V17 Crypto Sniper** is a high-precision, mathematical quantitative framework designed to systematically grow a modest capital (\$50) to institutional scale (\$1,000+) using:
1. **Smart Money Concepts (SMC)**: Strict 3-Order-Block structural sandwich, trading ONLY the 2nd (Middle) continuation OB.
2. **Outer Boundary Precision**: Pre-calculated entry strictly locked to the Top Boundary (`ob_high`) on 1st tap pullback.
3. **Institutional Order Flow Confirmation**: Real-time Cumulative Volume Delta (CVD) absorption, Whale Open Interest ($\Delta OI > +0.5\%$) expansion, and clean overhead airspace.
4. **Triple-Layer Risk Armor**: Soft candle close invalidation backed by an active **-16% Hard Airbag Stop Loss** on the exchange, Fee-Shield Breakeven, and a 2-Loss Daily Circuit Breaker.

---

## 2. The Golden 3-OB Chart Setup & Entry Rule

```
               ▲ HIGHER HIGH RESISTANCE
               │
          ┌────┴──────────────────────────┐
          │  1st OB (Topmost Resistance)  │  ◄── Overhead Ceiling (Airspace Target)
          └───────────────────────────────┘
                        │  
                        ▼  Clean Pullback (Price Coming Down From Above)
          ┌───────────────────────────────┐  ◄── 🎯 ENTRY POINT: 1st Tap at TOP BOUNDARY (ob_high)
          │  2nd OB (👑 MIDDLE TRADED OB) │
          └───────────────────────────────┘  ◄── Invalidation Floor
                        │
          ┌─────────────┴─────────────────┐
          │  3rd OB (Deepest Demand Floor)│
          └───────────────────────────────┘
```

### 👑 The Selection Rule:
* Jab bhi chart par 3 Order Blocks bante hain, hum na to 1st par trade karenge aur na hi 3rd par.
* **Hum strictly 2nd (Middle) OB par hi trade plan karenge.**

### 🎯 Pre-Calculated Entry Price (1st Tap Long):
$$\mathbf{\text{Entry Price}} = \mathbf{OB_{\text{high}}} \quad (\text{Top Boundary of 2nd OB})$$
* **1st Tap Execution**: Jaise hi live price 2nd OB ki Top Boundary ko pehli baar touch karega, wahi hamara exact entry price hoga.
* **1-Tick Front-Run**: Limit order ko exact boundary se **0.05% pehle (`ob_high * 1.0005`)** place kiya jayega taaki 100% limit fills milen aur slippage zero ho.

---

## 3. Timeframe Targets & Stop Loss Scorecard (5x Leverage)

| Metric | 1H Timeframe (Intraday Scalp) | 4H Timeframe (Macro Swing Sniper) |
| :--- | :--- | :--- |
| **Real Market Target Move** | **+1.60% Price Move** | **+2.40% Price Move** |
| **Target Profit ROE @ 5x** | **+8.00% ROE** | **+12.00% ROE** |
| **Soft Stop Loss (SL)** | **-10.00% ROE** (-2.00% move @ 5x) | **-11.25% (~11%) ROE** (-2.25% move @ 5x) |
| **Soft SL Rule** | **1H Candle Close** below level | **4H Candle Close** below level |
| **Emergency Hard SL (Exchange)**| **-16.00% ROE** (-3.20% move on exchange) | **-16.00% ROE** (-3.20% move on exchange) |
| **Fee-Shield Breakeven ($0 Net)**| Shift to $0 at **+0.75%** gain | Shift to $0 at **+1.05%** gain |

---

## 4. Institutional Order Flow Confluence (Rocket Ignition)

2nd OB level par tap aane par trade qualify hone ke liye 3 non-negotiable confluences chahiye:

1. **CVD Delta Absorption & Taker Buy Ratio $\ge 51\%$**:
   - Jab price 2nd OB Top Boundary par tap kare, to Cumulative Volume Delta niche girna band karke curl up ↗ hona chahiye aur aggressive market buying volume $51\%$ se zyada honi chahiye (passive sellers being absorbed).
2. **Whale Open Interest Expansion ($\Delta OI > +0.5\%$)**:
   - Touch ke time naye contracts add hone chahiye ($\Delta OI > +0.5\%$), jo confirm kare ki institutional whales long position build kar rahe hain.
3. **Overhead Airspace Room to 1st OB**:
   - 2nd OB aur 1st OB ke beech kam se kam:
     - 1H par: $\ge 1.65\%$ ka clean airspace gap (taaki +1.6% target bina resistance ke hit ho sake).
     - 4H par: $\ge 2.50\%$ ka clean airspace gap (taaki +2.4% target hit ho sake).

---

## 5. The Confirmed Safety Guardrails (Locked Rulebook)

1. **Hard Airbag SL (-16% ROE)**:
   - Soft SL candle close par chalega, lekin exchange par ek Hard Stop-Market order **-16.0% ROE (-3.20% price move)** par permanently active rahega taaki sudden crash wicks account ko liquidate na kar sakein.
2. **Fee-Protected Breakeven (True \$0.00 Net Loss)**:
   - Breakeven stop exact entry par nahi, balki **Entry Price + 0.10% buffer** par shift hoga. Trade Breakeven par nikalne ke baad exchange fees deduct hokar wallet me **Net Loss = True \$0.00** rahega.
3. **False Expansion & Minimum Qualification Distance**:
   - 2nd OB banne ke baad price jab tak kam se kam **+2.50% away (1H)** ya **+4.00% away (4H)** expand na ho jaye, tab tak OB qualified nahi hoga. Chop/sideways fakeouts 100% eliminate.
4. **Institutional Time-Stop (Dead Capital Protection)**:
   - Agar trade open hone ke baad **16 Hours (1H)** ya **48 Hours (4H)** me TP/BE hit nahi hota, to use Market Exit kar diya jayega taaki continuous funding fees se balance na kate.
5. **Blow-Off Climax Volume Filter**:
   - Displacement volume average volume se **1.4x se 3.5x** hona chahiye. Volume > 3.5x with giant upper wick (> 40%) hone par trade disqualify.
6. **Bid-Ask Spread Guard ($\le 0.08\%$)**:
   - Order execution se pehle live Bid-Ask Spread check hoga. Agar spread **> 0.08%** hai (high news volatility), to trade hold par rahega.
7. **Mandatory ISOLATED Margin Lock**:
   - Exchange par order hamesha **Strictly ISOLATED Margin** mode me execute hoga. Cross margin strictly prohibited hai.
8. **Weekend Altcoin Filter**:
   - Saturday aur Sunday ko risky altcoins pause rahenge (sirf BTC/ETH allow honge).
9. **Daily (1D) Macro Conflict Filter**:
   - Agar Daily (1D) trend violent crash / bearish hai (Daily close below 20 EMA / RSI < 35), to 1H/4H Long trades strictly block rahenge.
10. **2-Loss Daily Circuit Breaker**:
    - 24 ghante ke andar **2 Stop Loss** hit hote hain, to system agle **12 ghante ke liye AUTO-COOL-OFF (Freeze)** mode me chala jayega.
11. **Stage 1 Single-Position Rule**:
    - \$50 se \$100 tak ke dauran ek time par **sirf 1 position** open hogi.

---

## 6. The 3-Stage Mathematical Compounding Progression

| Stage | Capital Range | Allocation Policy | Target Profit / Trade | Est. Clean Trades to Target |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1: Survival & Foundation** | **\$50.00 ➔ \$100.00** | 100% Balance in 1 Trade (Max 1 Open) | +8.0% (1H) / +12.0% (4H) | **~8 to 10 Clean Trades** |
| **Stage 2: Acceleration** | **\$100.00 ➔ \$350.00** | 50% Margin (\$50 x 2 trades max) | +8.0% (1H) / +12.0% (4H) | **~12 to 14 Trades** |
| **Stage 3: Institutional Scale** | **\$350.00 ➔ \$1,000.00** | 30% Margin per trade (Risk capped at 3-5%) | +8.0% (1H) / +12.0% (4H) | **~16 to 18 Trades** |

---

## 7. Standard Documentation & Codebase Blueprint

```
SMC_V17_TRADING_SYSTEM/
│
├── docs/                                # Standard Documentation Blueprint
│   ├── PRD.md                           # Product Requirements ($50 to $1,000 roadmap)
│   ├── ARCHITECTURE.md                  # System & Pipeline Architecture
│   ├── RULES.md                         # Complete Locked Rulebook & Guardrails
│   ├── DESIGN.md                        # Multi-Page UI/UX specs
│   ├── TASKS.md                         # Active Living Sprint Tracker
│   └── MEMORY.md                        # 238 Historical Trades Audit Ledger & Lessons
│
├── engine/                              # Quantitative Trading Engines
│   ├── smc_v17.py                       # 3-OB Middle Selection & Qualification Engine
│   ├── dual_timeframe_sniper.py         # 1H & 4H Dual Sniper Coordinator
│   ├── cvd_calculator.py                # Volume Delta & Absorption Detector
│   ├── oi_tracker.py                    # Whale Open Interest Tracker
│   └── trade_journal.py                 # Master Journal & Compounding Ledger
│
├── database/                            # Triple-Layer Persistence
│   ├── smc_v17.db                       # Local SQLite (Fast Edge Cache)
│   ├── mongo_client.py                  # MongoDB Atlas Free Tier NoSQL Driver
│   └── trade_journal_ledger.csv         # Universal Master CSV (238 Trades Preserved)
│
├── static/                              # 6 Dedicated Platform Pages
│   ├── index.html                       # Trading Terminal (Lightweight Charts)
│   ├── positions.html                   # Futures Positions & 2nd OB Limits
│   ├── compounding.html                 # $50 Compounding Roadmap & 238-Trade Journal
│   ├── brain.html                       # Mike AI Brain & 5-Agent Council
│   ├── signals.html                     # Live Signals & 50-Coin Zone Radar
│   └── settings.html                    # Settings, Telegram Alerts, Pine Script v5
│
├── app.py                               # FastAPI Application Gateway & Endpoints
├── config.py                            # Central System Configuration & Parameters
├── scanner.py                           # 50-Coin High-Speed Background Scanner
└── MASTER_SYSTEM_BLUEPRINT.md           # This Document (Master Architecture Reference)
```

---

## 8. Verification & Production Deployment

* **Live Web Platform**: [https://smc-ai-agent.onrender.com](https://smc-ai-agent.onrender.com)
* **GitHub Repository**: [https://github.com/as7812164-sketch/smc-ai-agent](https://github.com/as7812164-sketch/smc-ai-agent)
* **Local Desktop Mirror**: `C:\Users\power\Desktop\SMC_V17_MASTER_SYSTEM\SMC_V17_CODEBASE\`
* **Historical Trades Ledger**: 238 Verified Trades (Zero Data Lost).
