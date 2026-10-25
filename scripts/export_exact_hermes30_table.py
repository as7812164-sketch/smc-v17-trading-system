import json

with open("hermes30_1to2_oos_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)

trades = d["trades"]
lines = []
lines.append("| # | Pair | Side | TF | Entry Time (IST) | Entry ($) | TP ($) | SL ($) | Exit Time (IST) | Exit ($) | Duration | Outcome | Net P&L | Balance |")
lines.append("| :-: | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |")
for t in trades:
    side_icon = "LONG" if t["side"] == "LONG" else "SHORT"
    pnl_str = f"+${t['net_pnl_usdt']:.2f}" if t['net_pnl_usdt'] > 0 else f"-${abs(t['net_pnl_usdt']):.2f}"
    lines.append(f"| **{t['trade_id']:02d}** | {t['symbol']} | {side_icon} | {t['timeframe']} | {t['entry_time_str']} | {t['entry_price']:.4f} | {t['tp_price']:.4f} | {t['sl_price']:.4f} | {t['exit_time_str']} | {t['exit_price']:.4f} | {t['duration']} | **{t['outcome']}** | `{pnl_str}` | `${t['balance_after']:.2f}` |")

with open("exact_hermes30_table.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Successfully written exact_hermes30_table.md with 57 rows!")
