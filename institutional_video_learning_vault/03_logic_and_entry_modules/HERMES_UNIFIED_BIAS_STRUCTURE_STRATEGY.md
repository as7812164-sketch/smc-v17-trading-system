# 🏛️ HERMES UNIFIED BIAS + EP02 STRUCTURE + 4-FILTER STRATEGY (V2.0)

**Unified Sources Locked Together:**
1. **3 Bias Trilogy Videos (`Ep 16 + Ep 17 + Ep 13`):** Shoaib Khan (`c9IjcD1EINM`, `3PrIrbZottw`, `t_tag39MlaU`) — `POI <-> Liquidity` perpetual loop, 4 Market Movement Regimes (trade `POI -> Liquidity`, ban `Liquidity -> Liquidity`), Completed `M/W/D` Candle Liquidity + Inside Bar Mothers, `4-Step Swing Reversal Rule`, Defensive Mirrors, OTE / `0.50` Dealing Range, Heavy Truck BTC `1D` Gate.
2. **Verified Episode 02 Structure Mapping:** [`live_structure_mapping.py`](file:///C:/Users/power/.gemini/antigravity/brain/d07fbe6e-9f2a-4fa8-8bb2-3f2752574ef5/scratch/live_structure_mapping.py) & [`CausalStructureTracker`](file:///C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system/engine/hermes_unified_v2_engine.py) — Inside-Bar filtration, Strict Body-Close `BOS`/`CHoCH` (Zero Failed-BOS Wick Ratchet), Left-Side Valid Pullback `IDM` confirmation, `FAILED_CHOCH` / `FAILED_BOS` sweep detection, and Execution-Timeframe (`1H`) Structural Dealing Range.
3. **Calibrated 4-Filter OB / Volume / Dynamic Profit Armor Engine:** Zero retail indicators (`RSI`, `MACD`, `EMA`, `Bollinger Bands` permanently banned), 7-Condition Strongest/Strong OB Taxonomy, Volume Absorption (`>= 1.15x` `15m` / `>= 1.10x` `1H`), and `SMC_V1_30` / `HERMES_28` Profit Armor (`5x Isolated Margin`).

---

## 🎯 1. Complete Unified Filter Pipeline (Zero Retail Indicators)

Every trade signal MUST clear all layers in sequence:

### Layer 1 — Macro BTC "Heavy Truck" Gate (`Ep 13, 17`)
- **BTC `4H` Causal Brake:** Block `LONG`s if BTC `4H <= -2.0%`; block `SHORT`s if BTC `4H >= +2.0%`.
- **BTC `1D` 3-Day Momentum Flow:** `LONG` requires `BTC_1D_Close > BTC_1D_Close[3]`; `SHORT` requires `BTC_1D_Close < BTC_1D_Close[3]`.

### Layer 2 — Ep 17 Choppy Regime Block (`Liquidity -> Liquidity`) & Completed `1D` Liquidity
- **Daily Outside Double-Sweep Guard (`CompletedHTFLiquidityTracker`):** Track completed closed `1D` candles (preserving Mother Candle `H/L` across Inside Bars). Reject entries if the latest completed `1D` candle swept BOTH prior `PDH` and `PDL` and closed back inside (`last_bsl_sweep_revert and last_ssl_sweep_revert` = classic Regime 4 stop-hunt trap).
- **4H / 1H Structural Chop Trap Block (`is_choppy_liquidity_trap`):** Reject if `4H` or `1H` `CausalStructureTracker` logged BOTH `FAILED_CHOCH` and `FAILED_BOS` wick sweeps inside 8 bars without a structural body close.

### Layer 3 — Verified Ep 02 Structure & Execution Dealing Range (`CausalStructureTracker`)
- **Coin `4H` Bias + Valuation:** Tap requires `4H` 30-bar dealing range Discount (`<= 0.50`) for `LONG` / Premium (`>= 0.50`) for `SHORT`, and non-opposing `4H` swing momentum.
- **Execution-TF (`1H`) Ep 02 Structural Dealing Range Extremes Guard:** Check `tr_1h.dealing_range_pos(entry)`:
  - Reject `LONG` if `dr_1h > 0.65` (already extended into `1H` structural Premium!).
  - Reject `SHORT` if `dr_1h < 0.35` (already extended into `1H` structural Discount!).
- **Fresh Strict Body-Close `4H BOS` Freeze:** Reject counter-trend trades within `<= 6` `4H` bars (`24 hours`) of a real strict body-close `4H BOS` in the opposing direction.
- **Completed `1D` Runway / Defensive Mirror Gate:** If nearest opposing `PDH`/`PDL` sits `< 1.5%` from entry, require `>= 1` Defensive Mirror OB protecting the setup, OR `STRONGEST` OB grade, OR aligned `1H` structure trend.

### Layer 4 — 7-Condition OB Quality & Institutional Volume Absorption (`Ep 04, 15`)
- **POI Ranking:** `Order Block (Strongest/Strong) > Volume Imbalance > FVG`. Weak OBs (Type 1 same-color without sweep, Type 3 C2-breach, mid-leg floaters) strictly banned. First Tap Only + Same-TF Body Close invalidation.
- **Volume Absorption:** `>= 1.15x` 20-bar rolling average volume (`Scenario B 15m`), `>= 1.10x` (`Scenario A 1H`).

### Layer 5 — Dual-Scenario Execution & Profit Armor (`Ep 08, 16`)
- **⚔️ Scenario A (`4H/1D` Strong/Strongest OB → `1H` 4-Step Swing Reversal):**
  `1. Tap` → `2. 1H Impulsive Displacement (>= 1.1x ATR) + FVG + Swing Break (*MSS)` → `3. Retest of 1H FVG/OB` → `4. Expansion`.
- **⚡ Scenario B (`1H` Strongest/Strong OB → `15m` Sweep Reclaim):**
  `1. 1H OB Tap` + actual floor/roof sweep → `2. Within <= 2h (8 x 15m bars)`, `15m` body closes back inside OB with **`>= 18%` rejection wick**.
- **Risk & Compounding Armor (`5x Isolated Margin`):**
  - **`SMC_V1_30` Growth Armor (Primary):** `+3.0% TP / -3.0% SL / +2.0% BE / +2.5% Trail (+1.0% lock)`.
  - **`HERMES_28` Defensive Armor:** `+2.8% TP / -2.8% SL / +1.0% BE / +1.8% Trail (+1.0% lock)`.

---

## 📊 2. Empirical 1-Year Zero-Lookahead Verification (`20` Coins × `34,995` `15m` Bars, `0.10%` Fees)

### 🏆 Unified Tier 1: Balanced (`Scenario A` + `1H Strongest & Strong OBs`) — [`test_unified_clean.py`](file:///C:/Users/power/.gemini/antigravity/brain/d07fbe6e-9f2a-4fa8-8bb2-3f2752574ef5/scratch/test_unified_clean.py)
| Variant & Armor | Period | Trades (`A / B`) | TP / SL | Net Win % | Net Return | Profit Factor | `$500` Sim | Max DD |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `V1 Baseline` (`SMC_V1_30`) | Full 1-Yr | 28 (`6 / 22`) | 16 / 7 | 67.9% | +9.07R | 2.24 | $596.70 | 4.1% |
| **`UNIFIED FULL` (`SMC_V1_30`)** | **Full 1-Yr** | **21 (`4 / 17`)** | **14 / 4** | **`76.2%`** | **`+9.97R`** | **`3.39`** | **`$608.17`** | `4.1%` |
| — *In-Sample Split* | First 6M | 7 (`1 / 6`) | 4 / 2 | 71.4% | **`+2.10R`** | **`2.02`** | $520.83 | **`2.1%`** |
| — *Out-of-Sample Split* | Last 6M | 14 (`3 / 11`) | 10 / 2 | **`78.6%`** | **`+7.87R`** | **`4.75`** | $583.85 | `4.1%` |
| `V1 Baseline` (`HERMES_28`) | Full 1-Yr | 28 (`6 / 22`) | 9 / 5 | 42.9% | +4.07R | 1.73 | $540.90 | 4.5% |
| **`UNIFIED FULL` (`HERMES_28`)** | **Full 1-Yr** | **21 (`4 / 17`)** | **8 / 3** | **47.6%** | **`+4.96R`** | **`2.46`** | **`$551.00`** | `4.2%` |

### 🎯 Unified Tier 2: Ultra-Sniper (`Scenario A` + `1H Strongest Post-Sweep ONLY`)
| Variant & Armor | Period | Trades (`A / B`) | TP / SL | Net Win % | Net Return | Profit Factor | `$500` Sim | Max DD |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `V1 Sniper` (`SMC_V1_30`) | Full 1-Yr | 19 (`6 / 13`) | 11 / 4 | 68.4% | +7.03R | 2.67 | $573.84 | 2.1% |
| **`UNIFIED SNIPER` (`SMC_V1_30`)** | **Full 1-Yr** | **14 (`4 / 10`)** | **10 / 2** | **`78.6%`** | **`+7.87R`** | **`4.75`** | **`$583.85`** | **`2.1%`** |
| — *In-Sample Split* | First 6M | 5 (`1 / 4`) | 4 / 1 | 80.0% | **`+2.83R`** | **`3.74`** | $528.65 | `2.1%` |
| — *Out-of-Sample Split* | Last 6M | 9 (`3 / 6`) | 6 / 1 | 77.8% | **`+5.03R`** | **`5.72`** | $552.21 | `2.1%` |
| **`UNIFIED SNIPER` (`HERMES_28`)** | **Full 1-Yr** | **14 (`4 / 10`)** | **6 / 1** | **57.1%** | **`+5.21R`** | **`5.29`** | **`$554.20`** | **`2.1%`** |
| — *IS / OOS Split (`HERMES_28`)* | IS / OOS | 5 / 9 | 0 SL / 1 SL | 40% / 66.7% | `+1.82R` / `+3.39R` | `18.0` / `4.06` | `$518.36` / `$534.57` | `0.1%` / `2.1%` |
