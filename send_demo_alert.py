import sys, asyncio
sys.path.append(r"C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system")
from alerts.telegram_service import TelegramService

DEMO_MSG = """🎯 <b>HERMES 2.0 APEX • TAKE PROFIT HIT!</b> 🏆
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱ <i>26 Sep 2026 • 04:30 PM IST | Sequential Trade #002</i>
🔥 <b>Win Streak:</b> <code>2 in a Row! (100.0% WR)</code>

<blockquote>🪙 <b>TRADE EXECUTION TICKET:</b>
• <b>Coin Pair:</b> <code>#NEARUSDT</code>
• <b>Setup:</b> 4H Extreme Order Block
• <b>Direction:</b> 🔴 SHORT (5x Isolated)
• <b>Entry Price:</b> <code>$4.8210</code>  ➜  <b>Exit TP:</b> <code>$4.6860</code> (+2.8%)
• <b>Duration:</b> <code>3h 48m (1 bar)</code>
• <b>Sniper Precision:</b> <code>98.1% (Drawdown sirf -0.38%)</code>

💰 <b>THIS TRADE PROFIT:</b>
├─ 💵 <b>Net Profit:</b> <code>+$14.85 USDT</code> (+24.41% ROE)
├─ 🏦 <b>Cold Vault (15%):</b> <code>+$2.23 USDT</code> (Banked Safely)
└─ 🚀 <b>Compounding (85%):</b> <code>+$12.62 USDT</code> (Added to Pool)</blockquote>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>TODAY'S DAILY PERFORMANCE SCORECARD</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 <b>Today's Net Profit:</b> <code>+$27.59 USDT</code> (+55.18% Growth)
🔢 <b>Completed Trades:</b> <code>2 Trades (2 Wins • 0 Losses)</code>
🎯 <b>Daily Win Rate:</b> <code>100.0% Precision</code>
🧭 <b>Direction:</b> 🟢 <b>LONG:</b> 1W/0L  |  🔴 <b>SHORT:</b> 1W/0L

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏦 <b>COMPOUNDING ROADMAP ($50 ➔ $2,000)</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💼 <b>Active Compounding Pool:</b> <code>$73.45 USDT</code>
🔒 <b>Cold Storage Vault:</b> <code>$4.14 USDT</code> (Profit Protected)
💎 <b>Total Account Equity:</b> <code>$77.59 USDT</code>

🎯 <b>Milestone Progress:</b>
<code>[██░░░░░░░░░░░░░░░░░░] 3.7% ($73.45 / $2,000.00)</code>

⚡ <b>NEXT TRADE POWER:</b>
├─ 💵 <b>Available Margin:</b> <code>$73.45 USDT</code>
├─ 🚀 <b>5x Buying Power:</b> <code>$367.25 USDT</code>
└─ 🎯 <b>Next Pipeline Target:</b> <code>#UNIUSDT Short ($9.747)</code>

🏛️ <b>4-Sentries Verification Audit:</b>
├─ S1 (BTC Macro): <code>PASS (Neutral +0.07%)</code>
├─ S2 (Displacement): <code>PASS (+6.4% + Bear FVG)</code>
├─ S3 (IDM Sweep): <code>PASS (24% Rejection Wick)</code>
└─ S4 (Freshness): <code>PASS (Tap Bar 4 ≤ 28)</code>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

async def main():
    service = TelegramService()
    result = await service.send_raw_message(DEMO_MSG, parse_mode="HTML")
    if result and result.get("ok"):
        print("SUCCESS: Demo alert sent to Telegram!")
    else:
        print(f"FAILED: {result}")
    if service.session and not service.session.closed:
        await service.session.close()

if __name__ == '__main__':
    asyncio.run(main())
