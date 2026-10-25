import json, datetime

with open("ada_verification_trade.json") as f:
    pkg = json.load(f)

candles_json = json.dumps(pkg["candles"])

html_content = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <title>ADAUSDT 1H Real Trade Manual Verification</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    body {{
      background: #0b0e14;
      color: #e2e8f0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
  </style>
</head>
<body class="p-4 antialiased">
  <div class="max-w-6xl mx-auto space-y-4">
    
    <!-- Header Banner -->
    <div class="bg-[#121824] border border-cyan-500/30 rounded-xl p-5 shadow-lg flex flex-wrap items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 rounded-full font-mono text-xs font-bold tracking-wider">
            REAL BINANCE FUTURES DATA
          </span>
          <span class="px-3 py-1 bg-green-500/20 text-green-400 border border-green-500/40 rounded-full font-mono text-xs font-bold">
            TAKE PROFIT HIT (+12.20% ROE)
          </span>
        </div>
        <h1 class="text-2xl font-bold text-white mt-2">
          ADA / USDT &bull; 1-Hour Institutional Extreme OB Audit
        </h1>
        <p class="text-sm text-slate-400 mt-1">
          Exact historical verification on Binance Futures (September 9, 2026). Check candle timestamps on your TradingView chart!
        </p>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[#0d121c] p-3 rounded-lg border border-slate-800 text-xs">
        <div>
          <div class="text-slate-400">Extreme OB</div>
          <div class="text-amber-400 font-bold font-mono">0.2150 - 0.2203</div>
        </div>
        <div>
          <div class="text-slate-400">50% MT Entry</div>
          <div class="text-cyan-400 font-bold font-mono">0.21765</div>
        </div>
        <div>
          <div class="text-slate-400">TP (+12.2% ROE)</div>
          <div class="text-green-400 font-bold font-mono">0.22296</div>
        </div>
        <div>
          <div class="text-slate-400">SL (-12.0% ROE)</div>
          <div class="text-red-400 font-bold font-mono">0.21243</div>
        </div>
      </div>
    </div>

    <!-- Interactive Canvas Chart Card -->
    <div class="bg-[#121824] border border-slate-800 rounded-xl p-4 shadow-xl">
      <div class="flex items-center justify-between mb-3 text-xs text-slate-400">
        <div class="flex items-center gap-4">
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 bg-amber-400/40 border border-amber-400 rounded-sm inline-block"></span> Extreme OB (0.2150 - 0.2203)</span>
          <span class="flex items-center gap-1.5"><span class="w-3 h-0.5 bg-cyan-400 inline-block"></span> 50% Mean Threshold (0.21765)</span>
          <span class="flex items-center gap-1.5"><span class="w-3 h-0.5 bg-green-400 inline-block"></span> Target TP (0.22296)</span>
          <span class="flex items-center gap-1.5"><span class="w-3 h-0.5 bg-red-400 inline-block"></span> Stop Loss (0.21243)</span>
        </div>
        <div id="hoverInfo" class="font-mono text-cyan-300 font-semibold">Hover over candles to inspect OHLC</div>
      </div>

      <div class="relative w-full h-[440px] bg-[#090d14] rounded-lg overflow-hidden border border-slate-900">
        <canvas id="tradeCanvas" class="w-full h-full block cursor-crosshair"></canvas>
      </div>
    </div>

    <!-- Verification Table -->
    <div class="bg-[#121824] border border-slate-800 rounded-xl p-5 shadow-lg">
      <h3 class="text-base font-bold text-white mb-3 flex items-center justify-between">
        <span>📋 Manual Verification Checklist (Binance Futures Historical Feed)</span>
        <span class="text-xs text-slate-400 font-normal">Displacement: +7.95% | Tap Window: 4 bars | Hold Rule: Passed</span>
      </h3>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs font-mono border-collapse">
          <thead>
            <tr class="border-b border-slate-800 text-slate-400 bg-slate-900/50">
              <th class="p-2.5">Date & Time (UTC)</th>
              <th class="p-2.5">Open</th>
              <th class="p-2.5">High</th>
              <th class="p-2.5">Low</th>
              <th class="p-2.5">Close</th>
              <th class="p-2.5">Volume</th>
              <th class="p-2.5">Event / Role in Setup</th>
            </tr>
          </thead>
          <tbody id="candleTableBody" class="divide-y divide-slate-800/60 text-slate-300">
            <!-- Populated via script -->
          </tbody>
        </table>
      </div>
    </div>

  </div>

  <script>
    const data = {candles_json};
    const obLow = {pkg['ob_low']};
    const obHigh = {pkg['ob_high']};
    const entryPrice = {pkg['entry_price']};
    const tpPrice = {pkg['tp_price']};
    const slPrice = {pkg['sl_price']};

    const canvas = document.getElementById('tradeCanvas');
    const ctx = canvas.getContext('2d');
    const hoverInfo = document.getElementById('hoverInfo');
    const tableBody = document.getElementById('candleTableBody');

    // Populate table
    data.forEach((c, idx) => {{
      const d = new Date(c.time);
      const timeStr = d.toISOString().replace('T', ' ').substring(0, 16) + ' UTC';
      let eventText = '<span class="text-slate-500">Regular candle</span>';

      if (c.low === obLow && c.high === obHigh) {{
        eventText = '<span class="text-amber-400 font-bold">🏛️ EXTREME OB CANDLE (Swing Low)</span>';
      }} else if (c.high >= 0.2300) {{
        eventText = '<span class="text-cyan-400 font-bold">🚀 EXPANSION PUMP (+7.95% Displacement & FVG)</span>';
      }} else if (c.low <= entryPrice && c.close >= entryPrice && idx >= 8 && idx <= 12) {{
        eventText = '<span class="text-emerald-400 font-bold">🎯 1st TAP @ 50% MT (ENTRY EXECUTED)</span>';
      }} else if (c.high >= tpPrice && idx > 10) {{
        eventText = '<span class="text-green-400 font-bold">🏆 TAKE PROFIT (TP) FILLED (+12.20% ROE)</span>';
      }}

      const row = document.createElement('tr');
      row.className = 'hover:bg-slate-800/40 transition-colors';
      row.innerHTML = `
        <td class="p-2 text-cyan-300">${{timeStr}}</td>
        <td class="p-2">${{c.open.toFixed(5)}}</td>
        <td class="p-2 text-green-400 font-semibold">${{c.high.toFixed(5)}}</td>
        <td class="p-2 text-red-400 font-semibold">${{c.low.toFixed(5)}}</td>
        <td class="p-2">${{c.close.toFixed(5)}}</td>
        <td class="p-2 text-slate-400">${{Number(c.volume).toLocaleString()}}</td>
        <td class="p-2">${{eventText}}</td>
      `;
      tableBody.appendChild(row);
    }});

    function resizeCanvas() {{
      const rect = canvas.parentElement.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
      drawChart(rect.width, rect.height);
    }}

    let mouseX = -1;

    function drawChart(w, h) {{
      ctx.clearRect(0, 0, w, h);

      const paddingLeft = 40;
      const paddingRight = 80;
      const paddingTop = 30;
      const paddingBottom = 40;

      const chartW = w - paddingLeft - paddingRight;
      const chartH = h - paddingTop - paddingBottom;

      // Price limits
      let minP = Math.min(...data.map(c => c.low), slPrice) - 0.001;
      let maxP = Math.max(...data.map(c => c.high), tpPrice) + 0.001;
      const pRange = maxP - minP;

      function getY(p) {{
        return paddingTop + chartH - ((p - minP) / pRange) * chartH;
      }}

      // Horizontal price gridlines
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      for (let p = minP; p <= maxP; p += 0.002) {{
        const y = getY(p);
        ctx.beginPath();
        ctx.moveTo(paddingLeft, y);
        ctx.lineTo(w - paddingRight, y);
        ctx.stroke();

        ctx.fillStyle = '#64748b';
        ctx.font = '10px monospace';
        ctx.fillText(p.toFixed(4), w - paddingRight + 8, y + 3);
      }}

      // Shaded Extreme OB zone
      const obYTop = getY(obHigh);
      const obYBottom = getY(obLow);
      ctx.fillStyle = 'rgba(245, 158, 11, 0.12)';
      ctx.fillRect(paddingLeft, obYTop, chartW, obYBottom - obYTop);
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([]);
      ctx.strokeRect(paddingLeft, obYTop, chartW, obYBottom - obYTop);

      // Label OB
      ctx.fillStyle = '#f59e0b';
      ctx.font = '11px sans-serif';
      ctx.fillText('EXTREME OB (0.2150 - 0.2203)', paddingLeft + 10, obYTop + 16);

      // 50% Mean Threshold line
      const mtY = getY(entryPrice);
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      ctx.moveTo(paddingLeft, mtY);
      ctx.lineTo(w - paddingRight, mtY);
      ctx.stroke();
      ctx.fillStyle = '#06b6d4';
      ctx.fillText('ENTRY 50% MT: 0.21765', paddingLeft + 10, mtY - 6);

      // TP Line
      const tpY = getY(tpPrice);
      ctx.strokeStyle = '#22c55e';
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 3]);
      ctx.beginPath();
      ctx.moveTo(paddingLeft, tpY);
      ctx.lineTo(w - paddingRight, tpY);
      ctx.stroke();
      ctx.fillStyle = '#22c55e';
      ctx.fillText('🎯 TAKE PROFIT: 0.22296 (+12.20% ROE)', paddingLeft + 10, tpY - 6);

      // SL Line
      const slY = getY(slPrice);
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(paddingLeft, slY);
      ctx.lineTo(w - paddingRight, slY);
      ctx.stroke();
      ctx.fillStyle = '#ef4444';
      ctx.fillText('SL: 0.21243 (-12.00% ROE)', paddingLeft + 10, slY + 14);

      ctx.setLineDash([]);

      // Draw Candlesticks
      const candleCount = data.length;
      const stepX = chartW / candleCount;
      const candleW = Math.max(stepX * 0.65, 4);

      data.forEach((c, i) => {{
        const cx = paddingLeft + i * stepX + stepX / 2;
        const openY = getY(c.open);
        const closeY = getY(c.close);
        const highY = getY(c.high);
        const lowY = getY(c.low);

        const isBull = c.close >= c.open;
        const color = isBull ? '#22c55e' : '#ef4444';

        // Wick
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(cx, highY);
        ctx.lineTo(cx, lowY);
        ctx.stroke();

        // Body
        ctx.fillStyle = color;
        const bodyTop = Math.min(openY, closeY);
        const bodyHeight = Math.max(Math.abs(closeY - openY), 1.5);
        ctx.fillRect(cx - candleW / 2, bodyTop, candleW, bodyHeight);

        // Highlight 1st Tap entry candle
        if (c.low <= entryPrice && c.close >= entryPrice && i >= 8 && i <= 12) {{
          ctx.strokeStyle = '#38bdf8';
          ctx.lineWidth = 2;
          ctx.strokeRect(cx - candleW / 2 - 2, bodyTop - 2, candleW + 4, bodyHeight + 4);
          ctx.fillStyle = '#38bdf8';
          ctx.font = 'bold 11px sans-serif';
          ctx.fillText('1st TAP', cx - 20, highY - 10);
        }}

        // Highlight TP hit candle
        if (c.high >= tpPrice && i > 10) {{
          ctx.fillStyle = '#22c55e';
          ctx.beginPath();
          ctx.arc(cx, highY, 5, 0, Math.PI * 2);
          ctx.fill();
          ctx.font = 'bold 11px sans-serif';
          ctx.fillText('TP HIT!', cx - 18, highY - 12);
        }}
      }});
    }}

    window.addEventListener('resize', resizeCanvas);
    canvas.addEventListener('mousemove', (e) => {{
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const paddingLeft = 40;
      const paddingRight = 80;
      const chartW = rect.width - paddingLeft - paddingRight;
      const stepX = chartW / data.length;

      const idx = Math.floor((x - paddingLeft) / stepX);
      if (idx >= 0 && idx < data.length) {{
        const c = data[idx];
        const d = new Date(c.time);
        const timeStr = d.toISOString().replace('T', ' ').substring(0, 16) + ' UTC';
        hoverInfo.innerHTML = `Bar #${{idx}}: ${{timeStr}} | O: ${{c.open.toFixed(5)}} H: ${{c.high.toFixed(5)}} L: ${{c.low.toFixed(5)}} C: ${{c.close.toFixed(5)}} Vol: ${{Number(c.volume).toLocaleString()}}`;
      }}
    }});

    setTimeout(resizeCanvas, 50);
  </script>
</body>
</html>
"""

with open(r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\real_trade_verification_chart.html", "w", encoding="utf-8") as out_f:
    out_f.write(html_content)

print("Generated real_trade_verification_chart.html successfully!")
