import json

d = json.load(open("hermes25_3year_detailed_monthly.json", "r", encoding="utf-8"))
m4 = d["queue_4h"]["monthly"]

# Last 12 full continuous calendar months: October 2025 through September 2026
months_12 = [m for m in sorted(m4.keys()) if m >= "2025-10" and m <= "2026-09"]

print(f"{'Month':<8} | {'Total Trades':<14} | {'Overall WR%':<12} | {'Longs (W / L)':<16} | {'Long WR%':<10} | {'Shorts (W / L)':<16} | {'Short WR%':<10}")
print("-" * 95)

tot_t, tot_w, tot_l = 0, 0, 0
tot_lt, tot_lw = 0, 0
tot_st, tot_sw = 0, 0

for m in months_12:
    v = m4[m]
    w = v["wins"]
    l = v["total"] - w
    wr = round(w / v["total"] * 100.0, 1) if v["total"] > 0 else 0.0
    
    lw = v["long_wins"]
    ll = v["long_total"] - lw
    lwr = round(lw / v["long_total"] * 100.0, 1) if v["long_total"] > 0 else 0.0
    
    sw = v["short_wins"]
    sl = v["short_total"] - sw
    swr = round(sw / v["short_total"] * 100.0, 1) if v["short_total"] > 0 else 0.0
    
    tot_t += v["total"]
    tot_w += w
    tot_l += l
    tot_lt += v["long_total"]
    tot_lw += lw
    tot_st += v["short_total"]
    tot_sw += sw
    
    print(f"{m:<8} | {v['total']:2d} ({w:2d}W / {l:2d}L)    | {wr:>5.1f}%       | {v['long_total']:2d} ({lw:2d}W / {ll:2d}L)     | {lwr:>5.1f}%     | {v['short_total']:2d} ({sw:2d}W / {sl:2d}L)     | {swr:>5.1f}%")

print("-" * 95)
tot_wr = round(tot_w / tot_t * 100.0, 1)
tot_lwr = round(tot_lw / tot_lt * 100.0, 1)
tot_swr = round(tot_sw / tot_st * 100.0, 1)

print(f"{'TOTAL':<8} | {tot_t:2d} ({tot_w:2d}W / {tot_l:2d}L)   | {tot_wr:>5.1f}%       | {tot_lt:2d} ({tot_lw:2d}W / {tot_lt-tot_lw:2d}L)   | {tot_lwr:>5.1f}%     | {tot_st:2d} ({tot_sw:2d}W / {tot_st-tot_sw:2d}L)   | {tot_swr:>5.1f}%")
