import re

with open("static/pro_charts.html", "r", encoding="utf-8") as f:
    text = f.read()

# We need to add the klines loader and the new drawRealHeatmapView function
new_cg_engine = """
        // =============================================================
        // 7. AUTHENTIC 1:1 COINGLASS LIQUIDITY HEATMAP ENGINE
        // =============================================================
        let cgKlines = [];
        let cgLiquidationBands = [];
        let cgRange = "24h";
        let cgLevFilter = "all";

        async function fetchCoinglassKlines(sym) {
            try {
                const limit = (cgRange === "7d") ? 168 : ((cgRange === "3d") ? 72 : 36);
                const res = await fetch(`https://fapi.binance.com/fapi/v1/klines?symbol=${sym}&interval=1h&limit=${limit}`);
                const data = await res.json();
                cgKlines = data.map(d => ({
                    time: parseInt(d[0]),
                    open: parseFloat(d[1]),
                    high: parseFloat(d[2]),
                    low: parseFloat(d[3]),
                    close: parseFloat(d[4]),
                    volume: parseFloat(d[5])
                }));
                computeCoinglassLiquidityBands();
            } catch (err) {
                console.warn("Coinglass klines fetch error:", err);
            }
        }

        function setCoinglassRange(range) {
            cgRange = range;
            document.querySelectorAll("#cgControlsBar .cg-pill-group:first-child .cg-pill").forEach(p => p.classList.remove("active"));
            event.target.classList.add("active");
            fetchCoinglassKlines(currentSymbol);
            showToast(`CoinGlass range set to ${range.toUpperCase()}`);
        }

        function setCoinglassLev(lev) {
            cgLevFilter = lev;
            document.querySelectorAll("#cgControlsBar .cg-pill-group:last-child .cg-pill").forEach(p => p.classList.remove("active"));
            event.target.classList.add("active");
            computeCoinglassLiquidityBands();
            showToast(`CoinGlass leverage filter: ${lev.toUpperCase()}`);
        }

        function computeCoinglassLiquidityBands() {
            if (!cgKlines || cgKlines.length < 5) return;
            cgLiquidationBands = [];

            // Compute macro swing highs and lows
            const step = (lastMarkPrice > 1000) ? 25 : (lastMarkPrice > 10 ? 0.2 : 0.02);
            const poolMap = {};

            cgKlines.forEach((k, idx) => {
                const volFactor = Math.min(k.volume * 0.1, 50);

                // Multi-leverage tiers (100x: 1.0%, 50x: 2.0%, 25x: 4.0%)
                const tiers = [];
                if (cgLevFilter === "all" || cgLevFilter === "100x") tiers.push({ factor: 0.010, weight: 1.2, name: "100x" });
                if (cgLevFilter === "all" || cgLevFilter === "50x") tiers.push({ factor: 0.020, weight: 1.0, name: "50x" });
                if (cgLevFilter === "all" || cgLevFilter === "25x") tiers.push({ factor: 0.040, weight: 0.8, name: "25x" });

                tiers.forEach(t => {
                    // Short liquidations above swing highs
                    const shortLiqP = Math.round((k.high * (1 + t.factor)) / step) * step;
                    poolMap[shortLiqP] = (poolMap[shortLiqP] || 0) + volFactor * t.weight;

                    // Long liquidations below swing lows
                    const longLiqP = Math.round((k.low * (1 - t.factor)) / step) * step;
                    poolMap[longLiqP] = (poolMap[longLiqP] || 0) + volFactor * t.weight;
                });
            });

            // Convert to bands array
            const maxVal = Math.max(...Object.values(poolMap), 10.0);
            for (const [pStr, vol] of Object.entries(poolMap)) {
                const price = parseFloat(pStr);
                const norm = Math.min(1.0, vol / maxVal);
                if (norm > 0.05) {
                    cgLiquidationBands.push({
                        price: price,
                        volume: vol,
                        intensity: norm,
                        isShortLiq: (price > lastMarkPrice)
                    });
                }
            }
        }

        // --- 1:1 COINGLASS HEATMAP RENDER ENGINE ---
        function drawRealHeatmapView() {
            if (!ctxCanvas || !heatmapCanvas) return;
            const w = heatmapCanvas.width = heatmapCanvas.clientWidth;
            const h = heatmapCanvas.height = heatmapCanvas.clientHeight;
            ctxCanvas.clearRect(0, 0, w, h);

            // 1. Dark Coinglass Background
            ctxCanvas.fillStyle = "#070a14";
            ctxCanvas.fillRect(0, 0, w, h);

            if (!cgKlines || cgKlines.length < 5) {
                ctxCanvas.fillStyle = "rgba(0,240,255,0.7)";
                ctxCanvas.font = "14px 'JetBrains Mono'";
                ctxCanvas.fillText("Connecting to CoinGlass Liquidity Engine...", w / 2 - 140, h / 2);
                return;
            }

            // Price bounds across the klines & bands
            let allPrices = cgKlines.map(k => k.high).concat(cgKlines.map(k => k.low));
            cgLiquidationBands.forEach(b => allPrices.push(b.price));
            allPrices.push(lastMarkPrice);

            const pMin = Math.min(...allPrices) * 0.996;
            const pMax = Math.max(...allPrices) * 1.004;
            const pRange = pMax - pMin || 1.0;

            const timeCount = cgKlines.length;
            const candleW = (w - 120) / timeCount;
            const chartLeft = 20;

            // 2. Render Cyberpunk Grid Lines & Price Labels on Right
            ctxCanvas.strokeStyle = "rgba(255, 255, 255, 0.04)";
            ctxCanvas.lineWidth = 1;
            for (let i = 0; i < 8; i++) {
                const gy = 50 + i * ((h - 90) / 7);
                ctxCanvas.beginPath();
                ctxCanvas.moveTo(chartLeft, gy);
                ctxCanvas.lineTo(w - 70, gy);
                ctxCanvas.stroke();

                const labelP = pMax - (i / 7) * pRange;
                ctxCanvas.fillStyle = "#64748b";
                ctxCanvas.font = "10px 'JetBrains Mono'";
                ctxCanvas.fillText(`${labelP.toFixed(labelP < 1 ? 4 : 2)}`, w - 65, gy + 3);
            }

            // 3. RENDER COINGLASS THERMAL LIQUIDITY LAYERS (ACROSS ENTIRE BACKGROUND)
            cgLiquidationBands.forEach(band => {
                const by = h - ((band.price - pMin) / pRange) * (h - 90) - 45;
                const bandH = Math.max(5, band.intensity * 20);

                // Thermal Gradient Color (Coinglass Palette)
                const grad = ctxCanvas.createLinearGradient(0, by - bandH/2, 0, by + bandH/2);
                grad.addColorStop(0, "rgba(0,0,0,0)");
                
                if (band.intensity > 0.75) {
                    // Nuclear Red / Fiery Lava
                    grad.addColorStop(0.3, "rgba(255, 23, 68, 0.4)");
                    grad.addColorStop(0.5, "rgba(255, 0, 84, 0.9)");
                    grad.addColorStop(0.7, "rgba(255, 215, 0, 0.95)"); // White-Hot Yellow Core
                } else if (band.intensity > 0.45) {
                    // Golden Sunfire / Yellow
                    grad.addColorStop(0.5, "rgba(255, 215, 0, 0.7)");
                } else if (band.intensity > 0.25) {
                    // Emerald Green
                    grad.addColorStop(0.5, "rgba(0, 230, 118, 0.5)");
                } else {
                    // Cyan / Indigo Base
                    grad.addColorStop(0.5, "rgba(0, 180, 216, 0.3)");
                }
                grad.addColorStop(1, "rgba(0,0,0,0)");

                ctxCanvas.fillStyle = grad;
                ctxCanvas.fillRect(chartLeft, by - bandH/2, w - 90, bandH);
            });

            // 4. RENDER REAL CANDLESTICKS ON TOP OF HEATMAP
            cgKlines.forEach((k, idx) => {
                const cx = chartLeft + idx * candleW;
                const isBull = k.close >= k.open;

                const oY = h - ((k.open - pMin) / pRange) * (h - 90) - 45;
                const cY = h - ((k.close - pMin) / pRange) * (h - 90) - 45;
                const hY = h - ((k.high - pMin) / pRange) * (h - 90) - 45;
                const lY = h - ((k.low - pMin) / pRange) * (h - 90) - 45;

                // Center Wick
                ctxCanvas.strokeStyle = isBull ? "rgba(0, 230, 118, 0.85)" : "rgba(255, 23, 68, 0.85)";
                ctxCanvas.lineWidth = 1.2;
                ctxCanvas.beginPath();
                ctxCanvas.moveTo(cx + candleW / 2, hY);
                ctxCanvas.lineTo(cx + candleW / 2, lY);
                ctxCanvas.stroke();

                // Candle Body
                const bodyTop = Math.min(oY, cY);
                const bodyH = Math.max(Math.abs(cY - oY), 2);
                ctxCanvas.fillStyle = isBull ? "#00e676" : "#ff1744";
                ctxCanvas.fillRect(cx + 2, bodyTop, Math.max(candleW - 4, 3), bodyH);
            });

            // 5. LIVE CURRENT MARK PRICE LASER LINE
            const curY = h - ((lastMarkPrice - pMin) / pRange) * (h - 90) - 45;
            ctxCanvas.strokeStyle = "#00f0ff";
            ctxCanvas.lineWidth = 2;
            ctxCanvas.setLineDash([6, 3]);
            ctxCanvas.beginPath();
            ctxCanvas.moveTo(chartLeft, curY);
            ctxCanvas.lineTo(w - 70, curY);
            ctxCanvas.stroke();
            ctxCanvas.setLineDash([]);

            // Mark Price Tag
            ctxCanvas.fillStyle = "#00f0ff";
            ctxCanvas.fillRect(w - 65, curY - 10, 60, 20);
            ctxCanvas.fillStyle = "#000000";
            ctxCanvas.font = "bold 10px 'JetBrains Mono'";
            ctxCanvas.fillText(`$${lastMarkPrice.toFixed(lastMarkPrice < 1 ? 4 : 2)}`, w - 62, curY + 4);

            // 6. TOP 2 MEGA LIQUIDATION CLUSTER ANNOTATIONS (COINGLASS CALLOUTS)
            const topShortLiq = cgLiquidationBands.filter(b => b.isShortLiq).reduce((m, b) => b.volume > (m ? m.volume : 0) ? b : m, null);
            if (topShortLiq) {
                const sY = h - ((topShortLiq.price - pMin) / pRange) * (h - 90) - 45;
                ctxCanvas.fillStyle = "rgba(255, 0, 84, 0.25)";
                ctxCanvas.strokeStyle = "#ff0054";
                ctxCanvas.lineWidth = 1.5;
                ctxCanvas.fillRect(30, sY - 22, 280, 22);
                ctxCanvas.strokeRect(30, sY - 22, 280, 22);

                ctxCanvas.fillStyle = "#ff80ab";
                ctxCanvas.font = "bold 10px 'JetBrains Mono'";
                ctxCanvas.fillText(`🔥 SHORT LIQ POOL: $${topShortLiq.price.toFixed(1)} ($${Math.round(topShortLiq.volume * 8.5)}M)`, 36, sY - 7);
            }

            const topLongLiq = cgLiquidationBands.filter(b => !b.isShortLiq).reduce((m, b) => b.volume > (m ? m.volume : 0) ? b : m, null);
            if (topLongLiq) {
                const lY = h - ((topLongLiq.price - pMin) / pRange) * (h - 90) - 45;
                ctxCanvas.fillStyle = "rgba(0, 230, 118, 0.25)";
                ctxCanvas.strokeStyle = "#00e676";
                ctxCanvas.lineWidth = 1.5;
                ctxCanvas.fillRect(30, lY + 4, 280, 22);
                ctxCanvas.strokeRect(30, lY + 4, 280, 22);

                ctxCanvas.fillStyle = "#b9f6ca";
                ctxCanvas.font = "bold 10px 'JetBrains Mono'";
                ctxCanvas.fillText(`🔥 LONG LIQ POOL: $${topLongLiq.price.toFixed(1)} ($${Math.round(topLongLiq.volume * 9.2)}M)`, 36, lY + 19);
            }
        }
"""

start_pos = text.find("function drawRealHeatmapView()")
end_pos = text.find("function drawFootprintView()")

if start_pos != -1 and end_pos != -1:
    text = text[:start_pos] + new_cg_engine + "\n        " + text[end_pos:]

# Also ensure fetchCoinglassKlines is called inside switchSymbol and on DOMContentLoaded
if "fetchCoinglassKlines(currentSymbol);" not in text:
    text = text.replace("initTradingView(currentSymbol);", "initTradingView(currentSymbol);\n            fetchCoinglassKlines(currentSymbol);")
    text = text.replace("initTradingView(sym);", "initTradingView(sym);\n            fetchCoinglassKlines(sym);")

with open("static/pro_charts.html", "w", encoding="utf-8") as f:
    f.write(text)

print("SUCCESS: 1:1 CoinGlass Liquidity Heatmap Engine injected into static/pro_charts.html!")
