# 🏛️ HERMES MSOB 4.0 — STEP 4 DUAL IMPLEMENTATION REGISTRY
## Engineering Specification & Source Code Architecture: Pine Script v5 Indicator & NexusPro Python Engine

---

### Executive Overview
This registry establishes the mathematical, architectural, and code-level parity between:
- **Part A: TradingView Pine Script v5 Indicator** (5m Chart Candle Mirror + Real vs Fake MSS Signals + Top-Right HUD).
- **Part B: NexusPro Autonomous Python Engine** (24/7 background 5m MSS Sentinel via free Binance Vision API).

---

## 💻 PART A: TRADINGVIEW PINE SCRIPT v5 IMPLEMENTATION

```pinescript
//@version=5
indicator("HERMES MSOB 4.0 - Step 4 Real MSS Sentinel", overlay=true, max_lines_count=100, max_labels_count=100)

// 1. Ingest Step 1 Macro Bias & Step 3 POI State
d_close   = request.security(syminfo.tickerid, "D", close, barmerge.gaps_off, barmerge.lookahead_off)
d_prev_h  = request.security(syminfo.tickerid, "D", high[1], barmerge.gaps_off, barmerge.lookahead_off)
d_prev_l  = request.security(syminfo.tickerid, "D", low[1], barmerge.gaps_off, barmerge.lookahead_off)
d_bias    = d_close > d_prev_h ? 1 : d_close < d_prev_l ? -1 : 0 // 1: Bullish, -1: Bearish

// 2. 5m 3-Bar Fractal Swings (STH & STL)
bool is_5m_stl = (low[1] < low[2]) and (low[1] < low[0])
bool is_5m_sth = (high[1] > high[2]) and (high[1] > high[0])

var float last_5m_sth = na
var float last_5m_stl = na
var int   last_5m_sth_bar = na
var int   last_5m_stl_bar = na

if is_5m_sth
    last_5m_sth := high[1]
    last_5m_sth_bar := bar_index[1]

if is_5m_stl
    last_5m_stl := low[1]
    last_5m_stl_bar := bar_index[1]

// 3. MSS Detection & Mandatory Candle Body Close Check
bool bull_breakout = not na(last_5m_sth) and ta.crossover(close, last_5m_sth) and (close > last_5m_sth)
bool bear_breakout = not na(last_5m_stl) and ta.crossunder(close, last_5m_stl) and (close < last_5m_stl)

// 4. The Universal Real vs Fake MSS Sentry Filter
bool is_real_bull_mss = bull_breakout and (d_bias == 1)
bool is_fake_bull_mss = bull_breakout and (d_bias == -1) // Inducement Trap

bool is_real_bear_mss = bear_breakout and (d_bias == -1)
bool is_fake_bear_mss = bear_breakout and (d_bias == 1)  // Inducement Trap

// 5. Visual Candle Mirror & Signals
plotshape(is_real_bull_mss, title="Real Bullish MSS", style=shape.triangleup, location=location.belowbar, color=color.green, size=size.small, text="REAL MSS ⚡")
plotshape(is_real_bear_mss, title="Real Bearish MSS", style=shape.triangledown, location=location.abovebar, color=color.red, size=size.small, text="REAL MSS ⚡")

plotshape(is_fake_bull_mss, title="Fake Bullish MSS", style=shape.xcross, location=location.abovebar, color=color.orange, size=size.tiny, text="TRAP (FAKE MSS)")
plotshape(is_fake_bear_mss, title="Fake Bearish MSS", style=shape.xcross, location=location.belowbar, color=color.orange, size=size.tiny, text="TRAP (FAKE MSS)")

// 6. HUD Dashboard Table Integration
var table hud = table.new(position.top_right, 2, 4, bgcolor=color.new(color.black, 20), border_color=color.gray, border_width=1)
if barstate.islast
    table.cell(hud, 0, 0, "HERMES MSOB 4.0", text_color=color.white, text_size=size.small)
    table.cell(hud, 1, 0, "STEP 4 MSS SENTINEL", text_color=color.aqua, text_size=size.small)
    
    table.cell(hud, 0, 1, "Macro Bias", text_color=color.white, text_size=size.tiny)
    table.cell(hud, 1, 1, d_bias == 1 ? "BULLISH 🟢" : d_bias == -1 ? "BEARISH 🔴" : "NEUTRAL ⚪", text_color=d_bias == 1 ? color.green : color.red, text_size=size.tiny)
    
    table.cell(hud, 0, 2, "5m Trigger Level", text_color=color.white, text_size=size.tiny)
    table.cell(hud, 1, 2, d_bias == 1 ? str.tostring(last_5m_sth, "#.##") : str.tostring(last_5m_stl, "#.##"), text_color=color.yellow, text_size=size.tiny)
    
    table.cell(hud, 0, 3, "Real MSS Status", text_color=color.white, text_size=size.tiny)
    table.cell(hud, 1, 3, is_real_bull_mss or is_real_bear_mss ? "ARMED: TRIGGERED 🎯" : "SCANNING ⚪", text_color=is_real_bull_mss or is_real_bear_mss ? color.green : color.gray, text_size=size.tiny)
```

---

## 🐍 PART B: NEXUSPRO AUTONOMOUS PYTHON ENGINE IMPLEMENTATION

```python
"""
HERMES MSOB 4.0 - Step 4 Autonomous Python Engine Module
Class: LTF_MSS_Engine
Role: 24/7 background 5m Real MSS & FVG detection with universal fake MSS suppression.
"""

from typing import List, Dict, Optional

class LTF_MSS_Engine:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def analyze_5m_structure_shift(self, klines_5m: List[Dict], htf_bias: str) -> Optional[Dict]:
        n = len(klines_5m)
        if n < 15:
            return None
            
        # Detect 3-bar fractals
        stls, sths = [], []
        for i in range(1, n - 2):
            if klines_5m[i]["low"] < klines_5m[i-1]["low"] and klines_5m[i]["low"] < klines_5m[i+1]["low"]:
                stls.append({"bar": i, "price": klines_5m[i]["low"]})
            if klines_5m[i]["high"] > klines_5m[i-1]["high"] and klines_5m[i]["high"] > klines_5m[i+1]["high"]:
                sths.append({"bar": i, "price": klines_5m[i]["high"]})
                
        # Bullish Analysis
        if htf_bias == "BULLISH" and sths and stls:
            lowest_bar = min(klines_5m[-25:], key=lambda x: x["low"])
            pre_swings = [s for s in sths if s["bar"] < lowest_bar["index"]]
            if pre_swings:
                trigger = pre_swings[-1]["price"]
                for j in range(lowest_bar["index"] + 1, n):
                    c = klines_5m[j]
                    if c["close"] > trigger: # Candle body close!
                        has_fvg = (j + 2 < n) and (klines_5m[j+2]["low"] > c["high"])
                        return {
                            "status": "REAL_MSS_CONFIRMED",
                            "direction": "BULLISH",
                            "trigger_level": trigger,
                            "break_price": c["close"],
                            "has_displacement_fvg": has_fvg,
                            "protected_floor": lowest_bar["low"]
                        }
                        
        # Bearish Analysis
        elif htf_bias == "BEARISH" and stls and sths:
            highest_bar = max(klines_5m[-25:], key=lambda x: x["high"])
            pre_swings = [s for s in stls if s["bar"] < highest_bar["index"]]
            if pre_swings:
                trigger = pre_swings[-1]["price"]
                for j in range(highest_bar["index"] + 1, n):
                    c = klines_5m[j]
                    if c["close"] < trigger: # Candle body close!
                        has_fvg = (j + 2 < n) and (klines_5m[j+2]["high"] < c["low"])
                        return {
                            "status": "REAL_MSS_CONFIRMED",
                            "direction": "BEARISH",
                            "trigger_level": trigger,
                            "break_price": c["close"],
                            "has_displacement_fvg": has_fvg,
                            "protected_ceiling": highest_bar["high"]
                        }
                        
        return None
```
