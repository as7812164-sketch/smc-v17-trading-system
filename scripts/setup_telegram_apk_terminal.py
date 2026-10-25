import os
import sys
import json
import ssl
import urllib.request
import urllib.parse

TOKEN = "8685685362:AAFWkKvRIs6cJ70gegcJVFyKB5soDtEttbU"
CHAT_ID = "752247227"
APK_PATH = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\static\HERMES_3.5_SINGLE_TIER_Trading_Terminal.apk"

def send_telegram_document(apk_file_path: str):
    print(f"Sending APK file {apk_file_path} to Telegram chat {CHAT_ID}...")
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    with open(apk_file_path, "rb") as f:
        file_bytes = f.read()

    body = []
    # chat_id field
    body.append(f"--{boundary}".encode())
    body.append(b'Content-Disposition: form-data; name="chat_id"')
    body.append(b'')
    body.append(CHAT_ID.encode())

    # caption field
    caption = (
        "📱 <b>BB 3.0 / NEXUSPRO APEX MOBILE TERMINAL (APK)</b>\n\n"
        "⚡ <b>Mobile App Version</b>: v2.5.0 Ultra-Responsive\n"
        "📐 <b>Screen Optimization</b>: 100% Full-Screen Mobile Fit\n"
        "🎯 <b>Features</b>: Live 15m Real-time Charts, 10 Deca Sections, BB Trailing SL Radar & Push Notifications.\n\n"
        "👇 <i>Neeche diye gaye APK file par tap karke seedha install karein.</i>"
    )
    body.append(f"--{boundary}".encode())
    body.append(b'Content-Disposition: form-data; name="caption"')
    body.append(b'')
    body.append(caption.encode())

    # parse_mode field
    body.append(f"--{boundary}".encode())
    body.append(b'Content-Disposition: form-data; name="parse_mode"')
    body.append(b'')
    body.append(b'HTML')

    # document field
    filename = "NexusPro_BB_Mobile_Terminal.apk"
    body.append(f"--{boundary}".encode())
    body.append(f'Content-Disposition: form-data; name="document"; filename="{filename}"'.encode())
    body.append(b'Content-Type: application/vnd.android.package-archive')
    body.append(b'')
    body.append(file_bytes)
    body.append(f"--{boundary}--".encode())
    body.append(b'')

    payload = b"\r\n".join(body)

    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    req = urllib.request.Request(url, data=payload)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    
    ctx = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            res = json.loads(resp.read().decode())
            if res.get("ok"):
                print("  [SUCCESS] APK document sent to Telegram successfully!")
            else:
                print(f"  [FAIL] Telegram returned: {res}")
    except Exception as e:
        print(f"  [ERROR] sendDocument exception: {e}")

def set_chat_menu_button():
    print("Setting persistent Web App Menu Button in Telegram...")
    url = f"https://api.telegram.org/bot{TOKEN}/setChatMenuButton"
    payload = {
        "chat_id": CHAT_ID,
        "menu_button": {
            "type": "web_app",
            "text": "📱 Open Terminal",
            "web_app": {
                "url": "https://nexuspro-terminal.onrender.com/trade"
            }
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    ctx = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            res = json.loads(resp.read().decode())
            if res.get("ok"):
                print("  [SUCCESS] Chat Menu Button set to '📱 Open Terminal' Web App!")
            else:
                print(f"  [FAIL] Menu button set returned: {res}")
    except Exception as e:
        print(f"  [ERROR] setChatMenuButton exception: {e}")

def send_terminal_portal_message():
    print("Sending Terminal Access Portal with interactive Mobile Web App buttons...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    text = (
        "🚀 <b>BB 3.0 / NEXUSPRO MOBILE TERMINAL PORTAL</b>\n\n"
        "Aapke mobile terminal ko Telegram ke sath link kar diya gaya hai. "
        "Aap bina browser khole, **seedha Telegram ke andar full mobile screen me** trade kar sakte hain!\n\n"
        "• <b>Real-Time Feeds</b>: BTC ($81k+) & 20 Champions live candlestick data\n"
        "• <b>Stepped Trailing SL</b>: Active live profit locking radar\n"
        "• <b>10 Deca Slots</b>: Isolated portfolio tracking\n\n"
        "<i>Neeche buttons par click karke turant terminal launch karein:</i>"
    )
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "⚡ Launch Futures Terminal (Full Mobile Screen)", "web_app": {"url": "https://nexuspro-terminal.onrender.com/trade"}}
            ],
            [
                {"text": "📊 Live Markets Radar", "web_app": {"url": "https://nexuspro-terminal.onrender.com/markets"}},
                {"text": "🧩 Deca Compounding", "web_app": {"url": "https://nexuspro-terminal.onrender.com/deca"}}
            ],
            [
                {"text": "🌐 Hologram 3D Hub", "web_app": {"url": "https://nexuspro-terminal.onrender.com/hologram"}}
            ]
        ]
    }
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    ctx = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            res = json.loads(resp.read().decode())
            if res.get("ok"):
                print("  [SUCCESS] Portal message with WebApp buttons sent successfully!")
            else:
                print(f"  [FAIL] SendMessage returned: {res}")
    except Exception as e:
        print(f"  [ERROR] sendMessage exception: {e}")

if __name__ == "__main__":
    send_telegram_document(APK_PATH)
    set_chat_menu_button()
    send_terminal_portal_message()
