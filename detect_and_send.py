import asyncio
import aiohttp
from database.db import set_setting
from alerts.telegram_service import telegram_service

TOKEN = "8593127726:AAGdudgSBU_krN-g42Cq_5ovc5DW2c6A-yY"

async def main():
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        async with session.get(url) as resp:
            data = await resp.json()

    results = data.get("result", [])
    if not results:
        print("No updates found yet.")
        return

    latest = results[-1]
    msg = latest.get("message") or latest.get("channel_post") or latest.get("my_chat_member")
    if not msg:
        print("Could not parse message from update:", latest)
        return

    chat = msg.get("chat", {})
    chat_id = str(chat.get("id"))
    first_name = chat.get("first_name", "")
    username = chat.get("username", "")

    print(f"Detected Chat ID: {chat_id} (User: {first_name} @{username})")

    # Save to database
    set_setting("telegram_chat_id", chat_id)
    set_setting("telegram_bot_token", TOKEN)

    # Send Live Status message
    status_text = telegram_service.build_live_status_text()
    send_resp = await telegram_service.send_raw_message(status_text)
    if send_resp and send_resp.get("ok"):
        msg_id = str(send_resp["result"]["message_id"])
        set_setting("telegram_status_msg_id", msg_id)
        print(f"SUCCESS: Live status message sent! Message ID: {msg_id}")
    else:
        print(f"Failed to send message: {send_resp}")

if __name__ == "__main__":
    asyncio.run(main())
