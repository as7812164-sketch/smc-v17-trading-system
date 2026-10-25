import json
from collections import defaultdict

data = json.load(open('last_7days_audit_results.json', encoding='utf-8'))
trades = data['trades']

days = defaultdict(lambda: {'total': 0, 'wins': 0, 'be': 0, 'loss': 0, 'open': 0, 'pnl': 0.0})

for t in trades:
    d = t['entry_time_str'][:6].strip()
    days[d]['total'] += 1
    out = t['outcome']
    if out == 'TP_HIT':
        days[d]['wins'] += 1
    elif out == 'BE_SAVE':
        days[d]['be'] += 1
    elif 'SL' in out:
        days[d]['loss'] += 1
    else:
        days[d]['open'] += 1
    if out != 'STILL_OPEN':
        days[d]['pnl'] += t['pnl_usdt']

print("DAY | TOTAL | WINS | BE | LOSS | OPEN | WIN RATE | NET PNL")
print("-" * 65)
for d in sorted(days.keys()):
    st = days[d]
    closed = st['wins'] + st['loss'] + st['be']
    wr = (st['wins'] / closed * 100) if closed > 0 else 0.0
    print(f"{d} | {st['total']:^5} | {st['wins']:^4} | {st['be']:^2} | {st['loss']:^4} | {st['open']:^4} | {wr:5.1f}%   | ${st['pnl']:+6.2f} USDT")
