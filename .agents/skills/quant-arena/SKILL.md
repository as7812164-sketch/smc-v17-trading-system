---
name: quant-arena
description: >-
  Quantitative Strategy Battle Arena for Antigravity. Pits multiple competing trading algorithms,
  SMC/ICT heuristics, Order Flow models, and hybrid execution engines against each other in standardized,
  adversarial Out-Of-Sample (OOS) trials to determine the supreme high-win-rate champion.
---

# 🏟️ Antigravity Quantitative Strategy Battle Arena

The **Quant Arena** is an adversarial multi-agent evaluation framework designed for institutional crypto and systematic trading systems. It prevents curve-fitting, exposes survivorship bias, and eliminates retail fallacies by subjecting candidate algorithms to identical, rigorous historical acid tests.

---

## 🏛️ Arena Rules & Governance

1. **Sacred Production Isolation**:
   - The live production trading engine (`engine/hermes35_live.py`) and live accounts are 100% frozen, read-only, and untouched.
   - All Arena gladiators compete inside sandboxed backtest and simulation engines.

2. **Standardized Battleground**:
   - All models run on identical historical datasets across the Top-25 Binance Futures pairs.
   - Zero lookahead bias: candle indices strictly enforced.
   - Standard execution conditions: \$50.00 initial capital, 5x isolated leverage, realistic 0.05% taker fee buffer.

3. **Auditor Elimination Matrix**:
   - **Win Rate Floor**: Any strategy achieving $< 75\%$ Win Rate is disqualified.
   - **Drawdown Ceiling**: Max Drawdown must remain $< 25\%$ under normal trading, $< 50\%$ under extreme multi-loss stress.
   - **Profit Factor Minimum**: Must maintain $> 2.0$ across 1-year continuous trading.
   - **Milestone Velocity**: Measured by trades required to compound \$50 to \$1,000.

---

## ⚔️ The 5 Competing Gladiators

| Gladiator ID | Designation | Core Logic & Edge | Loophole Addressed |
| :--- | :--- | :--- | :--- |
| **GLD-01** | **HERMES 3.5 Pure** | 5% Boundary Penetration + Bedrock Origin + Inducement Wick $\ge 18\%$ | Retail false OB trap |
| **GLD-02** | **SMT Intermarket Hunter** | Cross-Asset Divergence (BTC vs ETH vs SOL liquidity sweep) | Single-asset vacuum bias |
| **GLD-03** | **Killzone Temporal Sniper**| London (07:00-10:00 UTC) & NY (12:30-16:00 UTC) execution gates | Asian dead-zone chop |
| **GLD-04** | **CVD Delta Absorber** | Cumulative Volume Delta divergence & passive absorption | Fake breakout slicing |
| **GLD-05** | **QUANTUM HYBRID SUPREME** | Two-Stage Limit Tranche (50% @ 0.5% radar, 50% @ OB) + SMT + Killzone + CVD + Armor | Frequency bottleneck & missed entries |

---

## 🚀 Invocation & Execution

To execute the Quant Arena championship:
```bash
python run_quant_arena_championship.py
```

The script outputs a comprehensive comparative scorecard, individual gladiator metrics, Out-Of-Sample validation, and the Chief Quant Auditor's official certification verdict.
