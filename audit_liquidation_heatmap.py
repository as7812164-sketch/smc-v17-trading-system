import urllib.request
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def fetch_live_heatmap(symbol="BTCUSDT"):
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # 1. Fetch Order Book Depth (Top 500 levels)
    url_depth = f"https://fapi.binance.com/fapi/v1/depth?symbol={symbol}&limit=500"
    req = urllib.request.Request(url_depth, headers=headers)
    depth = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
    
    # 2. Fetch Open Interest & Mark Price
    url_oi = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}"
    oi_data = json.loads(urllib.request.urlopen(urllib.request.Request(url_oi, headers=headers), timeout=10).read().decode())
    total_oi_coins = float(oi_data["openInterest"])
    
    url_price = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
    mark_price = float(json.loads(urllib.request.urlopen(urllib.request.Request(url_price, headers=headers), timeout=10).read().decode())["price"])
    
    total_oi_usdt = total_oi_coins * mark_price

    print("=" * 70)
    print(f"🔥 LIVE BINANCE LIQUIDATION & LIQUIDITY HEATMAP AUDIT: {symbol}")
    print("=" * 70)
    print(f"👑 Live Mark Price: ${mark_price:,.2f}")
    print(f"📊 Total Active Open Interest: {total_oi_coins:,.2f} coins (~${total_oi_usdt:,.2f} USDT)")
    print("=" * 70)

    # Calculate Liquidity Buckets ($250 buckets)
    bucket_size = 250 if mark_price > 50000 else 10
    
    bids = [[float(p), float(q)] for p, q in depth["bids"]]
    asks = [[float(p), float(q)] for p, q in depth["asks"]]

    def bucket_depth(orders, is_bid=True):
        buckets = {}
        for p, q in orders:
            b_key = int(p // bucket_size) * bucket_size
            val_usdt = p * q
            buckets[b_key] = buckets.get(b_key, 0.0) + val_usdt
        return sorted(buckets.items(), key=lambda x: x[0], reverse=is_bid)

    bids_bucketed = bucket_depth(bids, True)
    asks_bucketed = bucket_depth(asks, False)

    print("\n🟢 TOP DEMAND / LONG STOP-LOSS LIQUIDATION CLUSTERS (BELOW PRICE):")
    print(f"{'Price Range':<22} | {'Depth (USDT)':<15} | {'Distance %':<12} | {'Type / Threat'}")
    print("-" * 70)
    for b_price, vol in bids_bucketed[:8]:
        pct_dist = (b_price - mark_price) / mark_price * 100.0
        threat = "MAJOR LONG LIQUIDATION WALL" if vol > 2_000_000 else "Stop-Loss Pool"
        print(f"${b_price:,.0f} - ${b_price + bucket_size:,.0f}    | ${vol/1e6:6.2f}M USDT   | {pct_dist:+6.2f}%     | {threat}")

    print("\n🔴 TOP SUPPLY / SHORT STOP-LOSS LIQUIDATION CLUSTERS (ABOVE PRICE):")
    print(f"{'Price Range':<22} | {'Depth (USDT)':<15} | {'Distance %':<12} | {'Type / Threat'}")
    print("-" * 70)
    for b_price, vol in asks_bucketed[:8]:
        pct_dist = (b_price - mark_price) / mark_price * 100.0
        threat = "MAJOR SHORT SQUEEZE WALL" if vol > 2_000_000 else "Stop-Loss Pool"
        print(f"${b_price:,.0f} - ${b_price + bucket_size:,.0f}    | ${vol/1e6:6.2f}M USDT   | {pct_dist:+6.2f}%     | {threat}")

    # Top overall pools
    top_bid = max(bids_bucketed, key=lambda x: x[1])
    top_ask = max(asks_bucketed, key=lambda x: x[1])
    print("=" * 70)
    print(f"🎯 BIGGEST LONG LIQUIDATION MAGNET BELOW: ${top_bid[0]:,.0f} (${top_bid[1]/1e6:.2f}M USDT)")
    print(f"🎯 BIGGEST SHORT SQUEEZE MAGNET ABOVE:   ${top_ask[0]:,.0f} (${top_ask[1]/1e6:.2f}M USDT)")
    print("=" * 70)

if __name__ == "__main__":
    fetch_live_heatmap("BTCUSDT")
