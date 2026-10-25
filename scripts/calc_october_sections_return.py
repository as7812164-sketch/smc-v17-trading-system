import sqlite3
import json
import urllib.request
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"

def get_live_render_deca():
    try:
        req = urllib.request.Request("https://smc-ai-agent.onrender.com/api/deca/sections", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.load(r)
            return data.get("sections", [])
    except Exception as e:
        print("Render sections fetch error:", e)
        return []

def get_live_render_status():
    try:
        req = urllib.request.Request("https://smc-ai-agent.onrender.com/api/status", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.load(r)
    except Exception as e:
        print("Render status fetch error:", e)
        return {}

def main():
    print("=" * 85)
    print("📊 OCTOBER 2026 RETURN BREAKDOWN AUDIT")
    print("=" * 85)

    # -------------------------------------------------------------
    # 1. LIVE RENDER DECA COMPOUNDING SECTIONS (4H MACRO vs 1H INTRADAY)
    # -------------------------------------------------------------
    r_secs = get_live_render_deca()
    if r_secs:
        # Group 1: 4H Macro Swing (Sections 1 to 5)
        macro_secs = [s for s in r_secs if int(s.get("id", 1)) <= 5]
        m_init = sum(float(s.get("initial_balance", 50.0)) for s in macro_secs)
        m_curr = sum(float(s.get("balance", s.get("current_balance", 50.0))) for s in macro_secs)
        m_pnl = m_curr - m_init
        m_roi = (m_pnl / m_init * 100.0) if m_init > 0 else 0.0
        m_wins = sum(int(s.get("win_count", 0)) for s in macro_secs)
        m_losses = sum(int(s.get("loss_count", 0)) for s in macro_secs)

        # Group 2: 1H Intraday (Sections 6 to 10)
        intra_secs = [s for s in r_secs if int(s.get("id", 1)) > 5]
        i_init = sum(float(s.get("initial_balance", 50.0)) for s in intra_secs)
        i_curr = sum(float(s.get("balance", s.get("current_balance", 50.0))) for s in intra_secs)
        i_pnl = i_curr - i_init
        i_roi = (i_pnl / i_init * 100.0) if i_init > 0 else 0.0
        i_wins = sum(int(s.get("win_count", 0)) for s in intra_secs)
        i_losses = sum(int(s.get("loss_count", 0)) for s in intra_secs)

        print("\n[VIEW A] LIVE DECA COMPOUNDING: 4H MACRO vs 1H INTRADAY SECTIONS (Current Live Status)")
        print("-" * 85)
        print(f"Group 1: 4H Macro Swing (Sections 1 to 5)")
        print(f"  • Starting Capital : ${m_init:.2f} USDT ($50 each)")
        print(f"  • Current Balance  : ${m_curr:.2f} USDT")
        print(f"  • Net Profit       : ${m_pnl:+.2f} USDT")
        print(f"  • Return %         : {m_roi:+.2f}%")
        print(f"  • Record           : {m_wins} Wins / {m_losses} Losses")

        print(f"\nGroup 2: 1H Intraday (Sections 6 to 10)")
        print(f"  • Starting Capital : ${i_init:.2f} USDT ($50 each)")
        print(f"  • Current Balance  : ${i_curr:.2f} USDT")
        print(f"  • Net Profit       : ${i_pnl:+.2f} USDT")
        print(f"  • Return %         : {i_roi:+.2f}%")
        print(f"  • Record           : {i_wins} Wins / {i_losses} Losses")

        print("-" * 85)
        tot_init = m_init + i_init
        tot_curr = m_curr + i_curr
        tot_pnl = tot_curr - tot_init
        tot_roi = (tot_pnl / tot_init * 100.0) if tot_init > 0 else 0.0
        print(f"Total Portfolio: ${tot_init:.2f} ➔ ${tot_curr:.2f} USDT | Net: ${tot_pnl:+.2f} USDT ({tot_roi:+.2f}%)")

    # -------------------------------------------------------------
    # 2. STRATEGY COMPARISON: BB 3.0 vs BB 3.5 IN OCTOBER 2026 (From Full 1-Year Audit)
    # -------------------------------------------------------------
    audit_file = os.path.join(ROOT_DIR, "scripts", "audit_1year_bb30_vs_bb35_results.json")
    if os.path.exists(audit_file):
        with open(audit_file, "r", encoding="utf-8") as f:
            audit = json.load(f)
        for m in audit.get("monthly_summary", []):
            if m.get("month") == "2026-10":
                bb30 = m.get("bb30", {})
                bb35 = m.get("bb35", {})
                print("\n" + "=" * 85)
                print("[VIEW B] STRATEGY PERFORMANCE: BB 3.0 vs BB 3.5 IN OCTOBER 2026 (1-16 Oct 2026)")
                print("=" * 85)
                print(f"1. BB 3.0 (Classic Stepped Trailing Sniper):")
                print(f"  • Total Trades : {bb30.get('total_trades')}")
                print(f"  • Win Rate     : {bb30.get('win_rate', 0):.1f}% ({bb30.get('wins')}W / {bb30.get('losses')}L / {bb30.get('saves')} Saves)")
                print(f"  • October ROI  : {bb30.get('roi_pct', 0):+.2f}% (Final Equity: ${bb30.get('final_equity', 0):.2f})")

                print(f"\n2. BB 3.5 (Dual-Confluence Wick & Momentum Filter):")
                print(f"  • Total Trades : {bb35.get('total_trades')}")
                print(f"  • Win Rate     : {bb35.get('win_rate', 0):.1f}% ({bb35.get('wins')}W / {bb35.get('losses')}L / {bb35.get('saves')} Saves)")
                print(f"  • October ROI  : {bb35.get('roi_pct', 0):+.2f}% (Final Equity: ${bb35.get('final_equity', 0):.2f})")
                print("=" * 85)

if __name__ == "__main__":
    main()
