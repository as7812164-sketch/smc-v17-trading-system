import urllib.request
import json

req = urllib.request.Request('https://smc-ai-agent.onrender.com/api/paper/sections', headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read())
print("Total Sections:", len(data['sections']))
for s in data['sections']:
    ot = s.get('open_trade')
    sym = ot['symbol'] if ot else 'IDLE (Ready for signal)'
    side = ot['side'] if ot else ''
    entry = ot['entry_price'] if ot else ''
    roi = ot.get('roi_pct', 0.0) if ot else ''
    print(f"Section {s['id']:02d} | TF: {s['timeframe'].upper():<2} | Status: {s['status']:<11} | Bal: ${s['balance']:.2f} | Trade: {sym} {side} (ROI: {roi}%)")

print("\nCombined Summary:")
print("Total Portfolio Balance: $", data['combined']['current_balance'])
print("Total Open Positions:   ", data['combined']['total_open_trades'])
print("Active Sections:        ", data['combined']['active_sections'])
print("Idle Sections Available:", 10 - data['combined']['active_sections'])
