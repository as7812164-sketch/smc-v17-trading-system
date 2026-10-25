with open("engine/bitget_trader.py", "r", encoding="utf-8") as f:
    text = f.read()

idx = 9500
print(text[idx:idx+2500].encode('ascii', 'replace').decode('ascii'))
