# 🔒 RULES: SMC V17 Crypto Sniper Core Trading Rules (LOCKED)

Yeh document system ke **Immutable Trading & Risk Rules** ko define karta hai. Yeh rules core engine (`engine/smc_v17.py`), scanner, visualizer aur test modules me permanently locked hain.

---

## 1. 3-OB Chart Structure & 2nd OB Selection Rule

Jab bhi chart par 3 Order Blocks (OBs) identify honge:
1. **1st OB (Topmost / Resistance)**: Highest recent swing high block. Overhead resistance ke roop me dekha jayega.
2. **2nd OB (Middle Block - 👑 THE TRADED ZONE)**: Continuation Re-accumulation block. **Hum strictly isi 2nd OB par trade plan karenge.**
3. **3rd OB (Bottom / Deepest Demand)**: Extreme structural origin.

---

## 2. Pre-Calculated Outer Boundary Entry (1st Tap Long Rule)

> [!IMPORTANT]
> **RULE #1 (ENTRY PRICE SELECTION)**:
> Jab price rally ke baad upar se niche pullback karega:
> $$\mathbf{\text{Entry Price}} = \mathbf{OB_{\text{high}}} \quad (\text{Top Boundary of 2nd OB})$$
> * **1st Tap Execution**: Jaise hi live price 2nd OB ki Top Boundary ko pehli baar touch karega, wahi hamara exact entry price hoga.
> * **Pre-Calculation**: Yeh entry price har coin ke liye pehle hi calculate hokar pending limit / alert me set rahega.
> * **Prohibited**: 2nd OB ke midpoint (50%) ya bottom boundary par long entry lagana strictly banned hai.

---

## 3. Timeframe-Specific Targets (TP) & Stop Loss (SL) Specifications

Leverage: **5x Isolated** (Strictly Fixed).

| Parameter | 1H Timeframe (Intraday Scalp) | 4H Timeframe (Macro Swing) |
| :--- | :--- | :--- |
| **Real Market Target Move** | **+1.60%** | **+2.40%** |
| **ROE Profit @ 5x Leverage** | **+8.00% ROE** ($1.60\% \times 5$) | **+12.00% ROE** ($2.40\% \times 5$) |
| **Soft Stop Loss (SL)** | **-10.00% ROE** (-2.00% price move @ 5x) | **-11.25% (~11%) ROE** (-2.25% price move @ 5x) |
| **Soft SL Execution Rule** | **1H Candle Close** below SL level ka wait karein | **4H Candle Close** below SL level ka wait karein |
| **Emergency Hard SL (Exchange)**| **-16.00% ROE** (-3.20% price move @ 5x) on exchange | **-16.00% ROE** (-3.20% price move @ 5x) on exchange |
| **Dynamic Breakeven ($0 Loss)**| Shift to $0 at **+0.75%** price gain (+3.75% ROE) | Shift to $0 at **+1.05%** price gain (+5.25% ROE) |

---

## 4. Advanced Institutional Confluence Filters (Candidate Strategy Suite)

2nd OB level par tap aane par target hit hone ki probability maximize karne ke liye proposed filters:

### 1. Cumulative Volume Delta (CVD) Absorption & Delta Ratio
* **Condition**: Taker Buy Volume / Total Volume $\ge 51\%$ to $60\%$.
* **CVD Reversal**: $CVD_{\text{current}} - CVD_{\text{previous}} > 0$ (Sellers absorb ho chuke hain, aggressive market buyers kick in kar rahe hain).

### 2. Whale Open Interest Expansion ($\Delta OI > +0.5\%$)
* **Condition**: Open interest net expansion hona chahiye, proving real institutional positioning rather than retail short covering.

### 3. Overhead Airspace Gap to 1st OB
* **Condition**: 2nd OB Top Boundary (`ob_high`) aur 1st OB Bottom Boundary (`top_ob_low`) ke beech kam se kam:
  - 1H par $\ge 1.65\%$ ka clear airspace gap hona chahiye taaki +1.6% target bina overhead friction ke hit ho sake.
  - 4H par $\ge 2.50\%$ ka clear airspace gap hona chahiye taaki +2.4% target hit ho sake.

### 4. 50 EMA Macro Trend Filter
* **Condition**: Price must be above 50 EMA on the traded timeframe to ensure trading strictly in the direction of the dominant institutional flow.

### 5. Pre-Displacement Liquidity Sweep (Turtle Soup)
* **Condition**: 2nd OB ki origin candle ne pichli 5-10 candles ke lows ko sweep karke liquidity absorb ki ho.

---

## 5. Security & Risk Guards

1. **Auto-Trading Default**: Strictly **PAUSED / OFF**.
2. **King Bitcoin Dump Shield**: Pause altcoin BUY entries if BTC dumps $> -1.5\%$ on 1H.
3. **Midnight 00:00 UTC Funding Guard**: No entries within 10 minutes of daily close / funding fee settlement.
4. **Master Ledger Maintenance**: Every backtest and live trade must be appended to `trade_journal_ledger.csv`, SQLite, and `docs/MEMORY.md` without dropping any historical data.

---

## 6. The Confirmed Compounding Safety Guardrails ($50 ➔ $1,000 Roadmap)

Yeh rules $50 se $1,000 tak compounding ke dauran account ko black-swan events, fee-drain aur execution slippage se 100% protect karne ke liye permanently locked hain:

1. **Rule 1: Fat OB & Hard SL -16% ROE (Sudden Dump Shield)**:
   - Fat OBs ke liye normal invalidation par **Candle Closing** ka wait karenge.
   - **Emergency Hard Stop Loss**: Market me sudden flash crash/dump aane par account ko protect karne ke liye exchange par **-16.0% ROE (-3.20% real price move)** ka Hard SL permanently placed rahega.
2. **Rule 2: [User Excluded]**:
   - Native bracket OCO complexity rule add nahi kiya gaya hai (per user specification).
3. **Rule 3: Upgraded Profit Targets (+8% ROE on 1H / +12% ROE on 4H)**:
   - **1H Target**: **+8.00% ROE** (+1.60% real market move @ 5x).
   - **4H Target**: **+12.00% ROE** (+2.40% real market move @ 5x).
4. **Rule 4: Weekend Altcoin Filter (ADDED)**:
   - Saturday aur Sunday ko low volume, CME closure aur fakeout wicks se bachne ke liye risky altcoin trading pause rahegi (sirf BTC/ETH allow honge).
5. **Rule 5: Daily (1D) Macro Conflict Filter (ADDED)**:
   - Agar Daily (1D) trend violently crashing / bearish hai (Daily close below 20 EMA / RSI < 35), to 1H ya 4H par Long trade strictly **DISQUALIFY / BLOCK** rahega.
6. **Rule 6: 2-Loss Daily Circuit Breaker (ADDED)**:
   - Agar 24 ghante ke andar **2 Stop Loss** hit hote hain, to system agle **12 ghante ke liye AUTO-COOL-OFF (Freeze)** mode me chala jayega taaki $50 capital drawdown spiral me na fasey.
7. **Rule 7: Fee-Shield Breakeven & Freshness Lock**:
   - Breakeven = Entry + 0.10% buffer (True $0.00 Net Loss after exchange fees).
   - Strictly 100% Fresh (Unmitigated) 2nd OBs only.

---

## 7. Institutional Microstructure & Execution Filters (Confirmed Points 1, 3, 4, 5, 6, 7)

Yeh 6 additional quantitative execution rules $50 ➔ $1,000 compounding ke liye mandatory aur permanently locked hain:

1. **Point 1: False Expansion & Minimum Qualification Distance**:
   - 2nd OB banne ke baad price jab tak structure break karke kam se kam:
     - **1H Timeframe**: Minimum **+2.50% away** expand na ho jaye.
     - **4H Timeframe**: Minimum **+4.00% away** expand na ho jaye.
     tab tak OB "Qualified" nahi mana jayega. Yeh rule chop/sideways range ke andar fake 2nd OB traps ko 100% eliminate karta hai.
2. **Point 3: Institutional Time-Stop (Dead Capital Protection)**:
   - Agar trade open hone ke baad:
     - **1H Timeframe**: **16 Hours** ke andar TP ya BE hit nahi hota.
     - **4H Timeframe**: **48 Hours** ke andar TP hit nahi hota.
     to trade ko Market Exit kar diya jayega taaki compounding capital dead na rahe aur continuous funding fees se balance drain na ho.
3. **Point 4: Blow-Off Climax Volume Filter**:
   - Displacement volume average volume se **1.4x se 3.5x** hona chahiye (Healthy Institutional Accumulation).
   - Agar volume **> 3.5x** hai with giant upper wick (> 40% of candle), to use "Whale Blow-Off Distribution" mark karke trade **DISQUALIFY** kiya jayega.
4. **Point 5: Bid-Ask Spread Guard ($\le 0.08\%$)**:
   - Order execution se pehle live Bid-Ask Spread check hoga. Agar spread **> 0.08%** hai (high volatility news wicks ya illiquidity), to trade tab tak hold par rahega jab tak spread normal na ho.
5. **Point 6: Mandatory ISOLATED Margin Lock**:
   - Bitget aur Binance API par order hamesha **Strictly ISOLATED Margin** mode me execute hoga. Cross margin strictly prohibited hai taaki bacha hua wallet balance hamesha 100% safe rahe.
6. **Point 7: Dynamic Exchange Step-Size / Lot Precision Rounding**:
   - Compounding balance badhne par har coin ke `min_qty` aur `step_size` ke hisaab se floor rounding execute hogi taaki exchange API `Precision Error` dekar order reject na kare.
