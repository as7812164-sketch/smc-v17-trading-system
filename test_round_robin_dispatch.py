import json

with open("oos_1year_deca_compounding_results.json", "r") as f:
    full_data = json.load(f)

# Re-run section simulation with Round-Robin dispatching
# Load all trades from the backtest
# In the previous script, we saved sample 50 trades, let's load candidate_signals from a clean script
