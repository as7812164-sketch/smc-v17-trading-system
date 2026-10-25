import json
import urllib.request
from datetime import datetime, timezone

def inspect_summary():
    # 1. Status API
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/status")
        status = json.loads(req.read().decode())
        print("=== SYSTEM STATUS ===")
        print("Hermes Status:", status.get("metrics", {}).get("hermes_status"))
        print("Binance Status:", status.get("metrics", {}).get("binance_status"))
        print("Paper Acc:", json.dumps(status.get("paper_trading", {}), indent=2))
        print("Performance:", json.dumps(status.get("performance", {}), indent=2))
    except Exception as e:
        print("Status error:", e)

    # 2. Open Positions
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/paper/positions")
        positions = json.loads(req.read().decode())
        print("\n=== OPEN POSITIONS ===")
        print(json.dumps(positions, indent=2))
    except Exception as e:
        print("Positions error:", e)

    # 3. Trade History
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/paper/trades")
        trades_data = json.loads(req.read().decode())
        trades = trades_data.get("trades", [])
        print(f"\n=== TRADES HISTORY (Total: {len(trades)}) ===")
        for i, t in enumerate(trades[:10], 1):
            sym = t.get("symbol")
            side = t.get("side")
            ep = t.get("entry_price")
            xp = t.get("exit_price")
            pnl = t.get("pnl_usdt")
            pnl_pct = t.get("pnl_pct") or t.get("roe_pct") or 0.0
            stat = t.get("status")
            dur = t.get("duration_str")
            mae = t.get("mae_pct")
            mfe = t.get("mfe_pct")
            t_ms = t.get("entry_time") or t.get("exit_time")
            t_str = datetime.fromtimestamp(t_ms / 1000, tz=timezone.utc).strftime("%d-%b %H:%M UTC") if t_ms else "N/A"
            print(f"#{i} {sym} | {side} | Status: {stat} | In: {ep} | Out: {xp} | PnL: ${pnl} ({pnl_pct}%) | Dur: {dur} | MAE: {mae}% | MFE: {mfe}% | Time: {t_str}")
    except Exception as e:
        print("Trades error:", e)

    # 4. Binance Live Status
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/binance/status")
        binance = json.loads(req.read().decode())
        print("\n=== BINANCE LIVE STATUS ===")
        print(json.dumps(binance, indent=2))
    except Exception as e:
        print("Binance status error:", e)

    # 5. Active Zones / Nearest Sentry Setups
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/signals/recent")
        sig = json.loads(req.read().decode())
        print("\n=== RECENT SIGNALS ===")
        print(f"Total recent signals: {len(sig.get('signals', []))}")
        for s in sig.get("signals", [])[:5]:
            print(f"{s.get('symbol')} | {s.get('side')} | Price: {s.get('entry_price')} | Score: {s.get('confluence_score')}")
    except Exception as e:
        print("Signals error:", e)

if __name__ == "__main__":
    inspect_summary()
