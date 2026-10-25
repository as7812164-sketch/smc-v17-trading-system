import sys, asyncio
sys.path.append(r"C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system")
from alerts.telegram_service import TelegramService

async def main():
    service = TelegramService()
    await service.send_raw_message('🧪 Demo alert: TP‑hit test message')
    # Clean up session
    if service.session and not service.session.closed:
        await service.session.close()

if __name__ == '__main__':
    asyncio.run(main())
