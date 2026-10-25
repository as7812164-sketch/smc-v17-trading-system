import json
import os

json_path = os.path.join(os.path.dirname(__file__), "..", "hermes30_july_oos_results.json")
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

trades = data["trades"]

lines = []
lines.append("| # | Symbol | Side | TF | Entry Time (IST) | Exit Time (IST) | Duration | Entry Price | TP Price | SL Price | Exit Price | Outcome | ROE % | Net P&L | Balance |")
lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")

for t in trades:
    outcome_badge = "**TP HIT**" if t["outcome"] == "TP_HIT" else ("*BE SAVE*" if t["outcome"] == "BE_SAVE" else "~~SL HIT~~")
    side_badge = "BUY" if t["side"] == "LONG" else "SELL"
    net_str = f"+${t['net_pnl_usdt']:.2f}" if t['net_pnl_usdt'] >= 0 else f"-${abs(t['net_pnl_usdt']):.2f}"
    
    line = (
        f"| {t['trade_id']} "
        f"| **{t['symbol']}** "
        f"| {side_badge} "
        f"| {t['timeframe']} "
        f"| {t['entry_time_str']} "
        f"| {t['exit_time_str']} "
        f"| {t['duration']} "
        f"| `{t['entry_price']}` "
        f"| `{t['tp_price']}` "
        f"| `{t['sl_price']}` "
        f"| `{t['exit_price']}` "
        f"| {outcome_badge} "
        f"| {t['roe_pct']:+.1f}% "
        f"| {net_str} "
        f"| **${t['balance_after']:.2f}** |"
    )
    lines.append(line)

out_md = "\n".join(lines)
out_path = os.path.join(os.path.dirname(__file__), "..", "exact_hermes30_july_table.md")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(out_md)

print("Exported", len(trades), "trades to exact_hermes30_july_table.md")
