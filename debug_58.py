import sys
sys.path.append(r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system")
import run_battle_hermes2_vs_hermes3_cvd_oi as r

orig_run = r.run_sequential_compounding
def custom_run(name, signals):
    signals.sort(key=lambda x: x["time"])
    executed = []
    active_exit = 0
    for s in signals:
        if s["time"] >= active_exit:
            executed.append(s)
            active_exit = s["exit_time"]
    cap = 50.0
    vault = 0.0
    for idx, trade in enumerate(executed):
        net_move = trade["gross"] - 0.0016
        pos_size = cap * 5.0
        pnl = pos_size * net_move
        if trade["res"] == "WIN":
            cap += (pnl * 0.85)
            vault += (pnl * 0.15)
        else:
            cap += pnl
        tot = cap + vault
        if 50 <= idx + 1 <= 75 and "Baseline" in name:
            print(f"[{name}] Trade #{idx+1}: {trade['res']} pnl=${pnl:,.2f} -> Cap=${cap:,.2f}, Vault=${vault:,.2f}, Total=${tot:,.2f}")
    return orig_run(name, signals)

r.run_sequential_compounding = custom_run
r.main()
