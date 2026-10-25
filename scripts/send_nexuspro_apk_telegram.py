import ssl
import urllib.request
import json
import os

TOKEN = "8685685362:AAFWkKvRIs6cJ70gegcJVFyKB5soDtEttbU"
CHAT_ID = "752247227"
APK_PATH = r"C:\Users\power\Desktop\NexusPro_Trading_Terminal.apk"

if not os.path.exists(APK_PATH):
    APK_PATH = r"C:\Users\power\Desktop\NexusPro_BB_3.0_Mobile_Terminal.apk"

with open(APK_PATH, "rb") as f:
    file_bytes = f.read()

boundary = "----NexusProApkBoundary982347"
body = []

# chat_id
body.append(f"--{boundary}".encode())
body.append(b'Content-Disposition: form-data; name="chat_id"')
body.append(b'')
body.append(CHAT_ID.encode())

# caption
caption = (
    "📱 <b>NEXUSPRO • INDEPENDENT ANDROID APP</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "✅ <b>Issue Resolved</b>: Package Name conflict fix kar diya gaya hai!\n"
    "📦 <b>New Unique Package</b>: <code>com.nexuspro.trading.terminal</code>\n"
    "🏷️ <b>App Label</b>: NexusPro\n\n"
    "✨ <b>Ab Dono Apps Side-by-Side Chalengi</b>:\n"
    "1️⃣ <b>HERMES APEX Terminal</b> (Pehle se installed)\n"
    "2️⃣ <b>NEXUSPRO Terminal</b> (Naya separate app)\n\n"
    "Koi 'Update' error nahi aayega, ab direct <b>'Install'</b> ka option aayega aur dono alag app bankar phone me rahenge!\n\n"
    "👇 <i>Neeche diye gaye file par tap karein aur Install dabayein:</i>"
)
body.append(f"--{boundary}".encode())
body.append(b'Content-Disposition: form-data; name="caption"')
body.append(b'')
body.append(caption.encode())

# parse_mode
body.append(f"--{boundary}".encode())
body.append(b'Content-Disposition: form-data; name="parse_mode"')
body.append(b'')
body.append(b'HTML')

# document
filename = "NexusPro_Trading_Terminal.apk"
body.append(f"--{boundary}".encode())
body.append(f'Content-Disposition: form-data; name="document"; filename="{filename}"'.encode())
body.append(b'Content-Type: application/vnd.android.package-archive')
body.append(b'')
body.append(file_bytes)
body.append(f"--{boundary}--".encode())
body.append(b'')

payload = b"\r\n".join(body)
url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
req = urllib.request.Request(url, data=payload, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
ctx = ssl._create_unverified_context()

try:
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        res = json.loads(resp.read().decode())
        if res.get("ok"):
            print("SUCCESS: NexusPro independent APK sent to Telegram successfully!")
        else:
            print("Telegram Error:", res)
except Exception as e:
    print("Error:", e)
