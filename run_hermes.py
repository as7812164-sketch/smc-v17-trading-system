"""
Hermes AI Command Line & Interactive Controller
Usage:
  python run_hermes.py --status      # View Hermes cognitive status & lifetime win rates
  python run_hermes.py --tune        # Run 6-month multi-asset parameter optimization
  python run_hermes.py --diagnose    # Forensic post-mortem on recent backtests / losses
  python run_hermes.py --scan        # Scan live markets and evaluate 15m/1h setups
  python run_hermes.py --chat "..."  # Conversational Q&A on strategy edges & insights
"""

import sys
import os
import json
import time
import argparse
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from ai.hermes_agent import hermes
from engine.hermes_optimizer import run_hermes_parameter_sweep

def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                 🧠 HERMES AI QUANTITATIVE TRADING AGENT                   ║
    ║        Institutional SMC V17 Strategy Enhancement & Optimization Engine   ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def cmd_status():
    print_banner()
    rep = hermes.get_status_report()
    print("=" * 75)
    print(f"  • Agent Name:               {rep['agent_name']}")
    print(f"  • Operating Status:         {rep['status']}")
    print(f"  • Lifetime Audited Trades:  {rep['total_trades_analyzed']}")
    print(f"  • Direct Win Rate (TP Hit): {rep['direct_win_rate_pct']}%")
    print(f"  • Capital Preservation:     {rep['capital_safety_rate_pct']}% (Wins + Fee-Shield BE)")
    print(f"  • Actual Loss Rate:         {rep['loss_rate_pct']}%")
    print(f"  • Active 15m Scalp Gap:     {rep['active_15m_airspace']}% Airspace")
    print(f"  • Active 1H Swing Gap:      {rep['active_1h_airspace']}% Airspace")
    print(f"  • Elite Assets:             {', '.join(rep['elite_assets'])}")
    print(f"  • Knowledge Base Insights:  {rep['total_lessons_recorded']} Institutional Lessons")
    print("=" * 75)
    print("\n[🧠 Recent Lessons Recorded in Memory]:")
    lessons = hermes.state.get("lessons_learned", [])[-3:]
    for l in lessons:
        print(f"  [{l['id']}] {l['title']} ({l['category']}):")
        print(f"      {l['insight']}\n")

def cmd_tune():
    print_banner()
    print("[*] Starting Hermes Multi-Asset Parameter Optimization Sweep...", flush=True)
    report = run_hermes_parameter_sweep()
    if report and "optimal_configuration" in report:
        best = report["optimal_configuration"]
        # Update hermes active parameters
        hermes.state.setdefault("parameters", {})["15m"]["airspace_req_pct"] = best["airspace_req_pct"]
        hermes.record_lesson(
            title=f"15m Scalp Airspace Optimized to {best['airspace_req_pct']}%",
            category="PARAMETER_TUNING",
            insight=f"Sweep over 360,000 candles verified that {best['airspace_req_pct']}% Airspace yields {best['win_rate_pct']}% direct Win Rate, {best['capital_safety_pct']}% Capital Safety, and grown $50.00 to ${best['final_balance']:,.2f} USDT (+{best['net_gain_pct']}%)."
        )
        print(f"[*] Hermes Knowledge Base successfully updated with fine-tuned parameters!", flush=True)

def cmd_diagnose():
    print_banner()
    ledger_path = Path("backtest_15m_6months_buy_ledger.csv")
    if not ledger_path.exists():
        print("[!] No 15m ledger file found. Run backtest first.")
        return

    import csv
    print(f"[*] Reading trades from {ledger_path}...", flush=True)
    trades = []
    with open(ledger_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trades.append(row)

    print(f"[*] Loaded {len(trades)} historical trades. Running Hermes Diagnostics...\n", flush=True)

    wins = [t for t in trades if t["Result"] == "WIN"]
    bes = [t for t in trades if t["Result"] in ("BREAKEVEN", "TIME_STOP_EXIT")]
    losses = [t for t in trades if "SL" in t["Result"]]

    print(f"  • Direct Wins: {len(wins)} | Breakevens: {len(bes)} | Losses: {len(losses)}\n")

    # Diagnose the sole loss
    for l in losses:
        diag = hermes.diagnose_trade({
            "symbol": l["Symbol"],
            "result": l["Result"],
            "airspace_pct": float(l.get("Airspace Gap %", 0.0)),
            "delta_ratio": float(l.get("Delta Ratio %", 50.0)),
            "minutes_held": int(l.get("Hold Time (Mins)", 0)),
            "date": l.get("Date (UTC)", "Unknown")
        })
        print(f"🔬 [DIAGNOSIS] {diag['symbol']} ({diag['date']}) - {diag['classification']}:")
        for k in diag["key_drivers"]:
            print(f"   - {k}")
        print(f"   💡 Recommendation: {diag['recommendation']}\n")

    # Sample diagnoses for win and breakeven
    if wins:
        w = wins[0]
        diag_w = hermes.diagnose_trade({
            "symbol": w["Symbol"],
            "result": w["Result"],
            "airspace_pct": float(w.get("Airspace Gap %", 0.0)),
            "delta_ratio": float(w.get("Delta Ratio %", 50.0)),
            "minutes_held": int(w.get("Hold Time (Mins)", 0)),
            "date": w.get("Date (UTC)", "Unknown")
        })
        print(f"🏆 [DIAGNOSIS SAMPLE WIN] {diag_w['symbol']} - {diag_w['classification']}:")
        for k in diag_w["key_drivers"]:
            print(f"   - {k}")
        print(f"   💡 Recommendation: {diag_w['recommendation']}\n")

def cmd_scan():
    print_banner()
    print("[*] Hermes Scanner: Fetching Live Market Data from Binance Futures (15m)...", flush=True)
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "AVAXUSDT", "SUIUSDT", "NEARUSDT", "1000PEPEUSDT", "XRPUSDT"]
    current_utc_hour = time.gmtime().tm_hour

    audited_setups = []

    for sym in symbols:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=15m&limit=80"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                raw = json.loads(r.read().decode())
        except Exception:
            continue

        candles = []
        running_cvd = 0.0
        for c in raw:
            vol = float(c[5])
            tb = float(c[9])
            delta = tb - (vol - tb)
            running_cvd += delta
            candles.append({
                "time": int(c[0]),
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
                "volume": vol,
                "taker_buy": tb,
                "cvd": running_cvd
            })

        if len(candles) < 50:
            continue

        # 50 EMA
        closes = [c["close"] for c in candles]
        mult = 2.0 / 51.0
        ema = sum(closes[:50]) / 50.0
        for k in range(50, len(closes)):
            ema = (closes[k] - ema) * mult + ema
        last_c = candles[-1]
        is_above_ema = last_c["close"] > ema

        # Check last candle order flow
        d_ratio = last_c["taker_buy"] / last_c["volume"] if last_c["volume"] > 0 else 0.50
        cvd_rev = candles[-1]["cvd"] > candles[-3]["cvd"]

        # Detect recent OB
        recent_downs = [c for c in candles[-25:-2] if c["close"] < c["open"]]
        if not recent_downs:
            continue
        ob_cand = recent_downs[-1]
        ob_h, ob_l = ob_cand["high"], ob_cand["low"]
        entry_est = ob_h * 1.0004
        airspace_est = 2.5 # approx placeholder for scan

        res = hermes.evaluate_live_setup(
            symbol=sym,
            timeframe="15m",
            entry_price=entry_est,
            ob_high=ob_h,
            ob_low=ob_l,
            airspace_pct=airspace_est,
            delta_ratio=d_ratio,
            cvd_reversal=cvd_rev,
            is_above_ema50=is_above_ema,
            utc_hour=current_utc_hour
        )
        audited_setups.append(res)

    audited_setups.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n{'='*85}")
    print(f"       HERMES LIVE 15-MINUTE MARKET AUDIT ({len(audited_setups)} Assets Scanned)")
    print(f"{'='*85}")
    for s in audited_setups:
        icon = "🟢" if s["score"] >= 75 else ("🟡" if s["score"] >= 60 else "⚪")
        print(f"  {icon} {s['symbol']:<12} | Score: {s['score']:>3}/100 | Verdict: {s['verdict']:<15} | Entry: ${s['entry_price']} | TP: ${s['tp_price']}")
        if s["cautions"]:
            print(f"     ⚠️ Cautions: {', '.join(s['cautions'][:2])}")
    print("=" * 85 + "\n")

def cmd_audit_strategy():
    print_banner()
    print("[*] Hermes Strategy Auditor: Reading Codebase & Identifying Loopholes...\n", flush=True)
    findings = hermes.audit_strategy_code()
    print("=" * 80)
    print("                HERMES FORENSIC STRATEGY AUDIT REPORT")
    print("=" * 80)
    print(f"  • Pine Script:        {findings['pine_script_status']}")
    print(f"  • Python Engine:      {findings['python_engine_status']}\n")
    print("  [🛡️ Core Operational Strengths]:")
    for r in findings["core_rules_identified"]:
        print(f"    ✓ {r}")
    print("\n  [⚠️ Loopholes Detected]:")
    for loop in findings["loopholes_detected"]:
        print(f"    • [{loop['severity']}] {loop['issue']}:")
        print(f"      {loop['detail']}")
    print("\n  [🚀 Recommended Institutional Upgrades]:")
    for up in findings["recommended_upgrades"]:
        print(f"    ➔ {up}")
    print("=" * 80 + "\n")

def cmd_patterns():
    print_banner()
    print("[*] Hermes Pattern Intelligence: Discovered Institutional Setups...\n", flush=True)
    patterns = hermes.discover_institutional_patterns()
    for idx, p in enumerate(patterns, 1):
        print(f"[{idx}] {p['pattern_name']}")
        print(f"    • Statistical Edge:   {p['backtest_statistics']}")
        print(f"    • Institutional Rationale: {p['institutional_rationale']}")
        print(f"    • Required Conditions:")
        for c in p['conditions']:
            print(f"       - {c}")
        print("-" * 75)

def cmd_enhance():
    print_banner()
    print("[*] Generating Hermes Strategy Enhancement Blueprint...\n", flush=True)
    bp = hermes.generate_strategy_enhancement_blueprint()
    print("=" * 80)
    print(f"       HERMES ENHANCEMENT BLUEPRINT: {bp['version']}")
    print("=" * 80)
    for key, p in bp["enhancement_pillars"].items():
        print(f"\n  👑 Pillar: {key.upper()}")
        print(f"     • Rule:            {p['rule']}")
        if "parameters" in p:
            print(f"     • Parameters:      {p['parameters']}")
        print(f"     • Expected Impact: {p['expected_impact']}")
    print("\n" + "=" * 80 + "\n")

def cmd_orchestrate(user_command: str):
    print_banner()
    print(f"[*] Hermes Multi-Agent Orchestrator: Dispatched command across 4 Subagents...\n", flush=True)
    report = hermes.orchestrate_command(user_command)
    print("=" * 80)
    print(f"  TASK:       {report['user_command']}")
    print(f"  TASK ID:    {report['task_id']}")
    print(f"  TIMESTAMP:  {report['timestamp']}")
    print(f"  DISPATCHED: {report['subagents_dispatched']} Concurrent Specialized Agents")
    print("=" * 80)
    for r in report["agent_reports"]:
        print(f"\n  🤖 Subagent: {r['agent'].upper()} [{r['status']}]")
        for f in r["findings"]:
            print(f"     • {f}")
    print("\n" + "=" * 80)
    print(f"  👑 EXECUTIVE VERDICT: {report['executive_verdict']}")
    print("=" * 80 + "\n")

def cmd_chat(prompt: str):
    print_banner()
    response = hermes.chat_query(prompt)
    print(response)

def main():
    parser = argparse.ArgumentParser(description="Hermes AI Quant Agent Controller")
    parser.add_argument("--status", action="store_true", help="View Hermes cognitive state & win rates")
    parser.add_argument("--audit-strategy", action="store_true", help="Read strategy code, detect loopholes & review rules")
    parser.add_argument("--patterns", action="store_true", help="View discovered zero-loss institutional patterns")
    parser.add_argument("--enhance", action="store_true", help="Generate institutional strategy enhancement blueprint")
    parser.add_argument("--tune", action="store_true", help="Run multi-asset strategy optimization")
    parser.add_argument("--diagnose", action="store_true", help="Perform forensic audit on trade ledger")
    parser.add_argument("--scan", action="store_true", help="Scan live market and score setups")
    parser.add_argument("--orchestrate", type=str, help="Auto-dispatch command across 4 concurrent subagents")
    parser.add_argument("--chat", type=str, help="Conversational query to Hermes")

    args = parser.parse_args()

    if args.status:
        cmd_status()
    elif args.audit_strategy:
        cmd_audit_strategy()
    elif args.patterns:
        cmd_patterns()
    elif args.enhance:
        cmd_enhance()
    elif args.tune:
        cmd_tune()
    elif args.diagnose:
        cmd_diagnose()
    elif args.scan:
        cmd_scan()
    elif args.orchestrate:
        cmd_orchestrate(args.orchestrate)
    elif args.chat:
        cmd_chat(args.chat)
    else:
        cmd_status()

if __name__ == "__main__":
    main()
