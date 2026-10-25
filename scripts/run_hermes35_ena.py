import sys, os, requests
sys.path.insert(0, os.getcwd())
from engine.hermes35_live import hermes35

print("=== RUNNING HERMES 3.5 SCANNER ON ENAUSDT ===")
try:
    setup_4h = hermes35.scan_symbol("ENAUSDT", "4h")
    print("ENA 4H Setup:", setup_4h)
except Exception as e:
    print("4H scan error:", e)

try:
    setup_1h = hermes35.scan_symbol("ENAUSDT", "1h")
    print("ENA 1H Setup:", setup_1h)
except Exception as e:
    print("1H scan error:", e)
