with open("engine/hermes30_apex_live.py", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("def detect_apex_setups_on_candles")
print(text[idx:idx+3500].encode('ascii', 'replace').decode('ascii'))
