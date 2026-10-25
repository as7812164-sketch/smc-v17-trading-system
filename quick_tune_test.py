import urllib.request
import json
import time
import sys
import numpy as np

# Let's test relaxing the Soft SL to the true OB Base (so it doesn't get prematurely stopped out by 0.1%)
from test_new_hybrid_risk_model import APPROVED_28_COINS, fetch_klines

def optimize_settings():
    print("Testing OB-Base Soft SL vs Arbitrary -8% SL...")
    # We will run the exact simulation with Soft SL at OB Base (rather than arbitrary -1.6%)
    
if __name__ == "__main__":
    optimize_settings()
