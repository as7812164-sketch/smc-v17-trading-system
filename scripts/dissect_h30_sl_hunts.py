import json
import os

data_path = os.path.join(os.path.dirname(__file__), "..", "sl_hunt_post_mortem_results.json")
with open(data_path, "r", encoding="utf-8") as f:
    res = json.load(f)

h30_sls = res["details"]["Hermes 3.0 Quantum"]
fake_hunts = [x for x in h30_sls if x["hit_tp_after_sl"]]

print(f"Total Hermes 3.0 Fake SL Hunts to dissect: {len(fake_hunts)}\n")

for i, t in enumerate(fake_hunts, 1):
    print(f"#{i} {t['month']} | {t['symbol']} {t['side']} {t['tf']} | Entry: {t['entry_time_str']} @ {t['ep']} | SL: {t['sl']} | TP: {t['tp']} | Hunted in: {t['time_to_sl_str']} -> Hit TP in: {t['time_from_sl_to_tp_str']}")
