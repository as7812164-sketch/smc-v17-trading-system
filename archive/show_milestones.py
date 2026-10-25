import json

with open('compounding_100days_result.json') as f:
    data = json.load(f)

trades = data['trades']
print(f"Total Trades evaluated: {len(trades)}")

for i, t in enumerate(trades):
    b = t['new_balance']
    prev = trades[i-1]['new_balance'] if i > 0 else 0
    if b >= 1000 and prev < 1000:
        print(f"[*] Milestone $1,000 crossed at Trade #{i+1} on {t['date']} | Balance: ${b:,.2f}")
    if b >= 5000 and prev < 5000:
        print(f"[*] Milestone $5,000 crossed at Trade #{i+1} on {t['date']} | Balance: ${b:,.2f}")
    if b >= 10000 and prev < 10000:
        print(f"[*] Milestone $10,000 crossed at Trade #{i+1} on {t['date']} | Balance: ${b:,.2f}")
    if b >= 50000 and prev < 50000:
        print(f"[*] Milestone $50,000 crossed at Trade #{i+1} on {t['date']} | Balance: ${b:,.2f}")
    if b >= 100000 and prev < 100000:
        print(f"[*] Milestone $100,000 crossed at Trade #{i+1} on {t['date']} | Balance: ${b:,.2f}")
