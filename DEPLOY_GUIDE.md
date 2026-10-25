# SMC V17 - 100% Free 24/7 Cloud Deployment Guide

Yeh guide aapko poora system **₹0 Free Cloud Server** par deploy karne me madad karegi, taaki aapka computer ya laptop band hone par bhi Telegram bot 24 ghante 365 din alerts bhejta rahe.

---

## 📦 Project Package Ready
Aapka clean deployment package already create ho chuka hai:
`C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\smc_v17_cloud_deployment.zip`

---

## 🚀 Tareeqa 1: Render.com (Sabse Aasan & Popular - 100% Free)

### Step 1: GitHub par Repository Banayein
1. [github.com](https://github.com) par jayein aur login karein (agar account nahi hai toh 1 minute me free ban jata hai).
2. Top right me **`+`** icon par click karke **`New repository`** select karein.
3. Repository name dein (e.g. `smc-v17-trading-system`).
4. **`Private`** select karein aur **`Create repository`** par click karein.
5. Page par **`uploading an existing file`** link par click karein aur project files (ya `smc_v17_cloud_deployment.zip` ko extract karke saari files) ko drag-and-drop karke **Commit changes** kar dein.

---

### Step 2: Render.com par Free Server Create Karein
1. [render.com](https://render.com) par jayein aur **Sign In with GitHub** karein.
2. Dashboard par **`New +`** button dabakar **`Web Service`** select karein.
3. Apni GitHub repository (`smc-v17-trading-system`) select karke **Connect** karein.
4. Settings fill karein:
   - **Name**: `smc-v17-live`
   - **Region**: `Singapore` (ya closest)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Instance Type**: **`Free`** ($0 / month)

---

### Step 3: Environment Variables (Telegram Credentials)
Niche **Environment Variables** section me yeh 2 keys add karein:
- **`TELEGRAM_BOT_TOKEN`** = `8593127726:AAGdudgSBU_krN-g42Cq_5ovc5DW2c6A-yY`
- **`TELEGRAM_CHAT_ID`** = `752247227`

Niche **`Create Web Service`** button par click karein!
Render 2 se 3 minute me aapka server live build kar dega aur aapko ek permanent free HTTPS URL de dega (e.g. `https://smc-v17-live.onrender.com`).

---

### Step 4: Server ko 24x7 Jagaye Rakhne Ka Free Hack (Keep-Alive)
Render ka free web service 15 minute bina request ke inactive ho jata hai. Isko 24/7 non-stop chalane ke liye:
1. [cron-job.org](https://cron-job.org) par free account banayein.
2. **`Create Cronjob`** par click karein.
3. Title: `SMC V17 Keep Alive`
4. URL: `https://smc-v17-live.onrender.com/api/status`
5. Schedule: **Every 10 minutes** (Har 10 minute me).
6. **Save** kar dein!
👉 Ab cron-job har 10 minute me aapke server ko ping karta rahega, jisse server **kabhi bhi sleep nahi hoga** aur 24 ghante background me 50 coins scan karke Telegram alerts bhejta rahega!

---

## ⚡ Tareeqa 2: Koyeb.com (Native 24/7 Free Nano Instance - Never Sleeps)
Koyeb ka free tier natively kabhi sleep nahi hota:
1. [koyeb.com](https://koyeb.com) par free signup karein.
2. **Create App** -> **GitHub** -> apni repo select karein.
3. Builder me **Dockerfile** select karein (hamne Dockerfile already bana rakha hai).
4. Environment variables me `TELEGRAM_BOT_TOKEN` aur `TELEGRAM_CHAT_ID` daalein.
5. **Deploy** dabayein. Yeh 24/7/365 bina kisi pinger ke non-stop run hota rahega!

---

## ✅ Deployment Ke Baad Kya Hoga?
1. Aapka laptop band ho ya on, server cloud par chalta rahega.
2. Telegram par First Tap entries, TP (+4%), aur SL (-3%) ke real-time alerts aate rahenge.
3. Aap apne phone ke browser se bhi cloud URL open karke live TradingView chart aur AI analysis dekh sakenge!
