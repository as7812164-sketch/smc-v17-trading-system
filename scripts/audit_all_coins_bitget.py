import sys
import os

sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader
import engine.hermes30_apex_live as h

print("Loading Bitget markets...")
markets = bitget_trader.exchange.load_markets()
print("Fetching all tickers at once...")
all_tickers = bitget_trader.exchange.fetch_tickers()

symbols = h.TOP_22_CHAMPIONS
margin_usdt = 5.0
leverage = 5.0
notional_usdt = margin_usdt * leverage # $25.00 notional

print(f"\nAUDITING {len(symbols)} COINS ON BITGET (Assuming $5.00 margin @ 5x = $25 Notional):")
issues = []
success_count = 0

for sym in symbols:
    ccxt_sym = bitget_trader.format_symbol_for_bitget(sym)
    market = markets.get(ccxt_sym)
    if not market:
        base = sym.replace("USDT", "")
        alt = f"{base}/USDT:USDT"
        market = markets.get(alt)
        if market:
            ccxt_sym = alt
        else:
            issues.append(f"MISSING MARKET: {sym} not listed on Bitget Futures")
            continue

    limits = market.get('limits', {})
    amt_limits = limits.get('amount', {})
    min_amt = amt_limits.get('min', 0.0) or 0.0
    cost_limits = limits.get('cost', {})
    min_cost = cost_limits.get('min', 0.0) or 0.0

    precision = market.get('precision', {})
    amt_prec = precision.get('amount')
    price_prec = precision.get('price')

    t = all_tickers.get(ccxt_sym, {})
    last_p = float(t.get('last') or t.get('close') or 1.0)
    raw_amt = notional_usdt / last_p
    
    # Test amount precision rounding
    try:
        clean_amt = float(bitget_trader.exchange.amount_to_precision(ccxt_sym, raw_amt))
        # If clean_amt is 0 because price is very high (e.g. BTC/ETH with small notional):
        if clean_amt <= 0:
            issues.append(f"ZERO AMOUNT: {sym} raw {raw_amt:.6f} rounded to 0.0! (Price: ${last_p})")
        elif clean_amt < min_amt:
            issues.append(f"MIN AMOUNT BREACH: {sym} clean amount {clean_amt} < min {min_amt} (Price: ${last_p})")
        else:
            calc_cost = clean_amt * last_p
            if calc_cost < min_cost:
                issues.append(f"MIN COST BREACH: {sym} cost ${calc_cost:.2f} < min ${min_cost}")
            else:
                success_count += 1
    except Exception as e:
        issues.append(f"PRECISION ERROR on {sym}: {e}")

print(f"\n--- AUDIT RESULTS ---")
print(f"Total Tested: {len(symbols)}")
print(f"Passed 100% Seamlessly: {success_count}")
print(f"Issues / Adjustments Needed: {len(issues)}")
for iss in issues:
    print("  *", iss)
