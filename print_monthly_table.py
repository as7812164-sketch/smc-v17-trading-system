import json

d = json.load(open("hermes25_3year_detailed_monthly.json", "r", encoding="utf-8"))
m4 = d["queue_4h"]["monthly"]
m1 = d["queue_1h"]["monthly"]
months = sorted(list(set(list(m4.keys()) + list(m1.keys()))))

print("Month   | 4H Trades (W/L) | 4H WR% | 4H Longs (WR%) | 4H Shorts (WR%) | 1H Trades (W/L) | 1H WR% | 1H Longs (WR%) | 1H Shorts (WR%)")
print("-" * 125)

for m in months:
    v4 = m4.get(m, {"total": 0, "wins": 0, "long_total": 0, "short_total": 0, "long_wins": 0, "short_wins": 0})
    v1 = m1.get(m, {"total": 0, "wins": 0, "long_total": 0, "short_total": 0, "long_wins": 0, "short_wins": 0})
    
    wr4 = round(v4["wins"] / v4["total"] * 100, 1) if v4["total"] > 0 else 0.0
    wr1 = round(v1["wins"] / v1["total"] * 100, 1) if v1["total"] > 0 else 0.0
    
    l_wr4 = round(v4["long_wins"] / v4["long_total"] * 100, 1) if v4["long_total"] > 0 else 0.0
    s_wr4 = round(v4["short_wins"] / v4["short_total"] * 100, 1) if v4["short_total"] > 0 else 0.0
    
    l_wr1 = round(v1["long_wins"] / v1["long_total"] * 100, 1) if v1["long_total"] > 0 else 0.0
    s_wr1 = round(v1["short_wins"] / v1["short_total"] * 100, 1) if v1["short_total"] > 0 else 0.0
    
    print(f"{m} | {v4['total']:2d} ({v4['wins']:2d}/{v4['total']-v4['wins']:2d})    | {wr4:5.1f}% | {v4['long_total']:2d} ({l_wr4:5.1f}%)   | {v4['short_total']:2d} ({s_wr4:5.1f}%)    | {v1['total']:2d} ({v1['wins']:2d}/{v1['total']-v1['wins']:2d})    | {wr1:5.1f}% | {v1['long_total']:2d} ({l_wr1:5.1f}%)   | {v1['short_total']:2d} ({s_wr1:5.1f}%)")
