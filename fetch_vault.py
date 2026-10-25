import urllib.request
import json

req = urllib.request.Request('https://raw.githubusercontent.com/as7812164-sketch/smc-ai-agent/data-vault/vault_state.json', headers={'User-Agent': 'Mozilla/5.0'})
try:
    data = json.loads(urllib.request.urlopen(req, timeout=10).read())
    print('Vault updated at:', data.get('timestamp'))
    open_t = [t for t in data.get('paper_trades', []) if t.get('status') == 'OPEN']
    print('Vault Open trades count:', len(open_t))
    for t in open_t:
        print(f"  #{t['id']}: {t['symbol']} {t['side']} ({t['timeframe']}) @ {t['entry_price']} | TP: {t['tp_price']} | SL: {t['sl_price']}")
    print('Vault accounts:')
    for a in data.get('accounts', []):
        print(f"  Acc #{a['id']}: balance={a['current_balance']}, pnl={a['total_pnl']}, W={a['win_count']}, L={a['loss_count']}")
except Exception as e:
    print('Vault fetch error:', e)
