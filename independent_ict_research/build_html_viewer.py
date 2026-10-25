import base64
import os

img_path = r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\btcusdt_pure_valid_ob_1791533459880.jpg"
with open(img_path, "rb") as f:
    b64_data = base64.b64encode(f.read()).decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
    <title>Hermes 4.0 Apex - 100% Pure Valid Order Block</title>
</head>
<body class="bg-[#0c1017] text-white p-4 font-sans">
    <div class="max-w-5xl mx-auto bg-[#121824] border border-[#1e293b] rounded-xl overflow-hidden shadow-2xl">
        <div class="flex items-center justify-between px-5 py-3 border-b border-[#1e293b] bg-[#161f30]">
            <div class="flex items-center space-x-3">
                <span class="px-2.5 py-1 bg-[#10b981]/20 text-[#10b981] border border-[#10b981]/40 rounded text-xs font-bold">100% PURE VALID OB CERTIFIED</span>
                <span class="text-sm font-semibold tracking-wide text-slate-200">BTC/USDT · 4H · Binance Futures (26 Nov - 02 Dec 2025)</span>
            </div>
            <div class="text-xs text-[#06b6d4] font-mono font-bold">+7.00% Spot (+35.0% ROE @ 5x) 🎯 R:R = 5.42:1</div>
        </div>
        <div class="p-3 bg-[#0a0d14] flex justify-center">
            <img src="data:image/jpeg;base64,{b64_data}" alt="BTC/USDT 4H 100% Valid Order Block Chart" class="w-full rounded-lg border border-[#1e293b] shadow-lg max-h-[650px] object-contain" />
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 bg-[#121824] border-t border-[#1e293b] text-xs">
            <div class="bg-[#161f30] p-2.5 rounded border border-[#1e293b]">
                <span class="text-slate-400 block">1. Prior Liquidity Swept:</span>
                <span class="font-bold text-[#f59e0b]">C2 Low ($86,306) &lt; C1 Low ($86,670)</span>
            </div>
            <div class="bg-[#161f30] p-2.5 rounded border border-[#1e293b]">
                <span class="text-slate-400 block">2. Virgin Fair Value Gap:</span>
                <span class="font-bold text-[#ec4899]">+$1,815 Imbalance Void (Untouched)</span>
            </div>
            <div class="bg-[#161f30] p-2.5 rounded border border-[#1e293b]">
                <span class="text-slate-400 block">3. Inducement (IDM):</span>
                <span class="font-bold text-[#06b6d4]">$90,907 Swept Before Retest</span>
            </div>
            <div class="bg-[#161f30] p-2.5 rounded border border-[#1e293b]">
                <span class="text-slate-400 block">4. Direct Entry @ 50% MT:</span>
                <span class="font-bold text-[#10b981]">$87,000 (33.8% Wick | R:R 5.42:1)</span>
            </div>
        </div>
    </div>
</body>
</html>"""

out_path = r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\trade_chart_viewer.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("trade_chart_viewer.html regenerated! Size:", os.path.getsize(out_path))
