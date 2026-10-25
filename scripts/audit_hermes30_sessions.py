import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from datetime import datetime, timezone, timedelta

import scripts.run_hermes30_model2a_10pct_and_deca_audit as h_audit

setups = h_audit.harvest_model2a_setups_with_limit_proximity()
print(f"Total Hermes 3.0 Model 2A Setups Harvested: {len(setups)}")

sessions = {
    "Asian Session (05:30 - 13:30 IST)": {"wins": 0, "saves": 0, "losses": 0, "tot_roi": 0.0},
    "London Session (13:30 - 18:30 IST)": {"wins": 0, "saves": 0, "losses": 0, "tot_roi": 0.0},
    "New York Session (18:30 - 02:30 IST)": {"wins": 0, "saves": 0, "losses": 0, "tot_roi": 0.0},
    "Pacific / Off-Hours (02:30 - 05:30 IST)": {"wins": 0, "saves": 0, "losses": 0, "tot_roi": 0.0}
}

count = 0
for s in setups:
    tr = h_audit.simulate_trade_with_stepped_trailing(s)
    ts = s["time"] / 1000.0
    ist_dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=5, minutes=30)))
    mins = ist_dt.hour * 60 + ist_dt.minute
    
    if 330 <= mins < 810:
        s_name = "Asian Session (05:30 - 13:30 IST)"
    elif 810 <= mins < 1110:
        s_name = "London Session (13:30 - 18:30 IST)"
    elif mins >= 1110 or mins < 150:
        s_name = "New York Session (18:30 - 02:30 IST)"
    else:
        s_name = "Pacific / Off-Hours (02:30 - 05:30 IST)"
        
    sec = sessions[s_name]
    out = tr.get("outcome", "")
    roi = tr.get("realized_roi", 0.0)
    sec["tot_roi"] += roi
    
    if "TRAILING_SL_HIT" in out:
        if tr.get("trailing_step", 0) > 1:
            sec["wins"] += 1
        else:
            sec["saves"] += 1 # Tier 1 is +1% ROI Fee-Shield Save
    elif roi > 0:
        sec["wins"] += 1
    elif abs(roi) <= 1.0:
        sec["saves"] += 1
    else:
        sec["losses"] += 1
    count += 1

print("\n" + "=" * 80)
print("🏛️ HERMES 3.0 MODEL 2A: 2-YEAR HISTORICAL SESSION PERFORMANCE REPORT")
print("=" * 80)

for s_name, data in sessions.items():
    tot = data["wins"] + data["saves"] + data["losses"]
    wr = (data["wins"] / tot * 100) if tot > 0 else 0
    safe_wr = ((data["wins"] + data["saves"]) / tot * 100) if tot > 0 else 0
    avg_roi = (data["tot_roi"] / tot) if tot > 0 else 0
    print(f"\n📍 {s_name}:")
    print(f"   Trades Count     : {tot} trades ({tot/count*100:.1f}% of total market activity)")
    print(f"   Pure Wins        : {data['wins']} ({wr:.1f}%)")
    print(f"   Fee-Shield Saves : {data['saves']} ({data['saves']/tot*100:.1f}%)")
    print(f"   Full Losses      : {data['losses']} ({data['losses']/tot*100:.1f}%)")
    print(f"   Capital Protection: {safe_wr:.1f}%")
    print(f"   Net Cumulative ROI: {data['tot_roi']:+,.1f}% (Avg ROI: {avg_roi:+.2f}% per trade)")
