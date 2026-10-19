import urllib.request
import urllib.parse
import json
import time

def heal_all():
    sections_data = [
        {"sec_id": 1, "restore_bal": 186.79, "win_count": 13, "loss_count": 0, "win_streak": 13},
        {"sec_id": 2, "restore_bal": 59.89,  "win_count": 5,  "loss_count": 1, "win_streak": 1},
        {"sec_id": 3, "restore_bal": 50.20,  "win_count": 2,  "loss_count": 0, "win_streak": 2},
        {"sec_id": 4, "restore_bal": 50.48,  "win_count": 2,  "loss_count": 0, "win_streak": 2},
        {"sec_id": 5, "restore_bal": 52.35,  "win_count": 1,  "loss_count": 0, "win_streak": 1},
        {"sec_id": 6, "restore_bal": 57.60,  "win_count": 12, "loss_count": 4, "win_streak": 0},
        {"sec_id": 7, "restore_bal": 64.98,  "win_count": 10, "loss_count": 3, "win_streak": 1},
        {"sec_id": 8, "restore_bal": 64.50,  "win_count": 4,  "loss_count": 0, "win_streak": 4},
        {"sec_id": 9, "restore_bal": 60.02,  "win_count": 2,  "loss_count": 0, "win_streak": 2},
        {"sec_id": 10, "restore_bal": 75.29, "win_count": 3,  "loss_count": 0, "win_streak": 3},
    ]

    for s in sections_data:
        params = urllib.parse.urlencode({
            "sec_id": s["sec_id"],
            "restore_bal": s["restore_bal"],
            "win_count": s["win_count"],
            "loss_count": s["loss_count"],
            "win_streak": s["win_streak"]
        })
        url = f"https://smc-ai-agent.onrender.com/api/admin/heal-trade?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            res = urllib.request.urlopen(req, timeout=15)
            print(f"Healed Section {s['sec_id']}: balance=${s['restore_bal']} -> {res.read().decode()}")
        except Exception as e:
            print(f"Error healing Section {s['sec_id']}: {e}")
        time.sleep(0.3)

if __name__ == "__main__":
    heal_all()
