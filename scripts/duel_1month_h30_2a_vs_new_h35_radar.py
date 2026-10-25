import os
import sys
import json

REPO_ROOT = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

from scripts.duel_hermes30_vs_hermes35_1week import load_1week_candles, simulate_hermes30_2a, CHAMPIONS
from scripts.test_hermes35_radar_new_rules_1month import load_1month_candles, backtest_hermes35_new_rules, PAIR_MAPPING

def run_1month_duel():
    h30_trades_all = []
    h35_trades_all = []
    
    for sym in CHAMPIONS:
        candles = load_1month_candles(sym, bars=2880)
        if len(candles) < 200:
            continue
            
        # 1. Hermes 3.0 Model 2A on 1 Month
        t30 = simulate_hermes30_2a(candles, leverage=5.0)
        for t in t30:
            t["symbol"] = sym
        h30_trades_all.extend(t30)
        
        # 2. New Hermes 3.5 Radar (4x, 50% MT 1st tap, 2:4 RRR, Stepped Trailing SL)
        t35 = backtest_hermes35_new_rules(candles, sym, leverage=4.0)
        h35_trades_all.extend(t35)

    def analyze_portfolio(trades, name, is_h35=False):
        trades.sort(key=lambda x: x.get("time", 0))
        total = len(trades)
        if total == 0:
            return {}
            
        sections = {str(i): {"balance": 50.0, "trades": 0, "wins": 0, "saves": 0, "losses": 0} for i in range(1, 11)}
        peak_eq = 500.0
        max_dd = 0.0
        
        pure_wins = 0
        saves = 0
        losses = 0
        
        total_r = 0.0
        gross_win_r = 0.0
        gross_loss_r = 0.0
        
        for t in trades:
            sec_id = str(PAIR_MAPPING.get(t["symbol"], 1))
            sec = sections[sec_id]
            risk_usd = sec["balance"] * 0.05
            
            if is_h35:
                # pnl_r is explicitly given
                pnl_r = t["pnl_r"]
                dollar_pnl = pnl_r * risk_usd
                if t["outcome"] in ["FULL_TP_WIN", "TRAILING_LOCK_WIN (+1.0R)"]:
                    pure_wins += 1
                elif "BE_FEE_SHIELD" in t["outcome"]:
                    saves += 1
                elif "LOSS" in t["outcome"]:
                    losses += 1
            else:
                # Hermes 3.0 Model 2A
                # roe: WIN is +15% ROE (+2.0R relative to 7.5% risk unit), BE is +0.5% ROE (+0.07R), LOSS is -7.5% ROE (-1.0R)
                if t["outcome"] == "WIN":
                    pnl_r = 2.0
                    pure_wins += 1
                elif t["outcome"] == "BE_SAVE":
                    pnl_r = 0.1
                    saves += 1
                elif t["outcome"] == "LOSS":
                    pnl_r = -1.0
                    losses += 1
                else:
                    pnl_r = t.get("roe", 0.0) / 7.5
                    if pnl_r > 0:
                        pure_wins += 1
                    else:
                        losses += 1
                        
                dollar_pnl = pnl_r * risk_usd
                
            total_r += pnl_r
            if pnl_r > 0:
                gross_win_r += pnl_r
            elif pnl_r < 0:
                gross_loss_r += abs(pnl_r)
                
            sec["balance"] += dollar_pnl
            sec["trades"] += 1
            if dollar_pnl > 0:
                sec["wins"] += 1
            elif dollar_pnl < 0:
                sec["losses"] += 1
            else:
                sec["saves"] += 1
                
            cur_eq = sum(s["balance"] for s in sections.values())
            if cur_eq > peak_eq:
                peak_eq = cur_eq
            dd = ((peak_eq - cur_eq) / peak_eq) * 100.0
            if dd > max_dd:
                max_dd = dd
                
        final_eq = sum(s["balance"] for s in sections.values())
        profit_usd = final_eq - 500.0
        roi_pct = (profit_usd / 500.0) * 100.0
        profit_factor = (gross_win_r / gross_loss_r) if gross_loss_r > 0 else 999.0
        pure_wr = (pure_wins / total) * 100.0
        qual_wr = ((pure_wins + saves) / total) * 100.0
        
        return {
            "name": name,
            "total_trades": total,
            "pure_wins": pure_wins,
            "be_saves": saves,
            "losses": losses,
            "pure_win_rate_pct": round(pure_wr, 2),
            "quality_win_rate_pct": round(qual_wr, 2),
            "total_net_pnl_in_r": round(total_r, 2),
            "profit_factor": round(profit_factor, 2),
            "starting_capital_usd": 500.00,
            "final_capital_usd": round(final_eq, 2),
            "net_profit_usd": round(profit_usd, 2),
            "portfolio_roi_pct": round(roi_pct, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "sections": sections
        }

    res_h30 = analyze_portfolio(h30_trades_all, "HERMES 3.0 MODEL 2A", is_h35=False)
    res_h35 = analyze_portfolio(h35_trades_all, "NEW HERMES 3.5 RADAR (4X + 50% MT 1ST TAP + 2:4 RRR + TRAILING SL)", is_h35=True)
    
    print("=" * 80)
    print("⚔️ 1-MONTH QUANT DUEL: HERMES 3.0 MODEL 2A vs NEW HERMES 3.5 RADAR HARVEST")
    print("Universe: Top-20 Champions | Period: 30 Days (2,880 15m Bars) | Capital: $500.00")
    print("=" * 80)
    print(json.dumps({"Hermes_30_Model_2A": res_h30, "New_Hermes_35_Radar": res_h35}, indent=2))
    
    with open(os.path.join(REPO_ROOT, "scratch", "duel_1month_h30_vs_new_h35.json"), "w", encoding="utf-8") as f:
        json.dump({"Hermes_30_Model_2A": res_h30, "New_Hermes_35_Radar": res_h35}, f, indent=2)

if __name__ == "__main__":
    run_1month_duel()
