import re

with open("static/pro_charts.html", "r", encoding="utf-8") as f:
    content = f.read()

# Replace drawRealHeatmapView and getSonogramThermalColor
old_func_start = content.find("function drawRealHeatmapView()")
old_func_end = content.find("function drawFootprintView()")

if old_func_start != -1 and old_func_end != -1:
    new_heatmap_code = """function drawRealHeatmapView() {
            if (!ctxCanvas || !heatmapCanvas) return;
            const w = heatmapCanvas.width = heatmapCanvas.clientWidth;
            const h = heatmapCanvas.height = heatmapCanvas.clientHeight;
            ctxCanvas.clearRect(0, 0, w, h);

            // Deep Obsidian Background
            ctxCanvas.fillStyle = "#04060a";
            ctxCanvas.fillRect(0, 0, w, h);

            // High-Tech Cyberpunk Horizontal & Vertical Grid
            ctxCanvas.strokeStyle = "rgba(255, 255, 255, 0.035)";
            ctxCanvas.lineWidth = 1;
            for (let y = 30; y < h; y += 30) {
                ctxCanvas.beginPath();
                ctxCanvas.moveTo(0, y);
                ctxCanvas.lineTo(w, y);
                ctxCanvas.stroke();
            }
            for (let x = 40; x < w; x += 60) {
                ctxCanvas.beginPath();
                ctxCanvas.moveTo(x, 0);
                ctxCanvas.lineTo(x, h);
                ctxCanvas.stroke();
            }

            // Top Header HUD
            ctxCanvas.fillStyle = "#00f0ff";
            ctxCanvas.font = "bold 12px 'JetBrains Mono'";
            ctxCanvas.fillText(`🔥 MULTI-LAYER LIQUIDITY DEPTH MATRIX (BOOKMAP / COINGLASS) - ${currentSymbol}`, 20, 24);

            // Calculate Dynamic Adaptive Price Range to stretch all 40 levels vertically
            let allPrices = [...orderbookBids.map(b => b[0]), ...orderbookAsks.map(a => a[0])];
            let minBookP = allPrices.length > 0 ? Math.min(...allPrices) : lastMarkPrice * 0.999;
            let maxBookP = allPrices.length > 0 ? Math.max(...allPrices) : lastMarkPrice * 1.001;
            let pad = Math.max((maxBookP - minBookP) * 0.15, (lastMarkPrice > 1000 ? 4.0 : 0.04));
            let pMin = minBookP - pad;
            let pMax = maxBookP + pad;
            let pRange = pMax - pMin || 1.0;

            const time = Date.now() * 0.001;

            // Global max volume for relative normalization
            let allSizes = [...orderbookBids.map(b => b[1]), ...orderbookAsks.map(a => a[1])];
            let maxBookSize = Math.max(...allSizes, 2.0);

            // RENDER VIBRANT HORIZONTAL DEPTH BANDS (ACROSS FULL WIDTH)
            // 1. Asks (Sellers / Resistance Pools Above Mark)
            orderbookAsks.forEach((a, idx) => {
                const price = a[0];
                const size = a[1];
                const sy = h - ((price - pMin) / pRange) * (h - 80) - 40;
                const norm = Math.min(1.0, Math.log10(1 + size * 8) / Math.log10(1 + maxBookSize * 8));
                const bandH = Math.max(4, norm * 18);

                // Thermal gradient band stretching across screen
                const grad = ctxCanvas.createLinearGradient(0, sy - bandH/2, 0, sy + bandH/2);
                grad.addColorStop(0, "rgba(255, 23, 68, 0)");
                if (norm > 0.6) {
                    grad.addColorStop(0.3, "rgba(255, 140, 0, 0.4)");
                    grad.addColorStop(0.5, "rgba(255, 235, 0, 0.9)"); // Bright Nuclear Yellow Core
                    grad.addColorStop(0.7, "rgba(255, 23, 68, 0.7)");
                } else if (norm > 0.3) {
                    grad.addColorStop(0.5, "rgba(0, 230, 118, 0.6)"); // Emerald Green
                } else {
                    grad.addColorStop(0.5, "rgba(0, 229, 255, 0.35)"); // Cyan Base
                }
                grad.addColorStop(1, "rgba(255, 23, 68, 0)");

                ctxCanvas.fillStyle = grad;
                const bandWidth = w - 180;
                ctxCanvas.fillRect(20, sy - bandH/2, bandWidth, bandH);

                // Right volume profile bar
                const barW = norm * 70;
                ctxCanvas.fillStyle = norm > 0.6 ? "rgba(255, 183, 3, 0.85)" : "rgba(0, 229, 255, 0.5)";
                ctxCanvas.fillRect(w - 170, sy - 2, barW, 4);

                // Price label on right
                ctxCanvas.fillStyle = "#cbd5e1";
                ctxCanvas.font = "9px 'JetBrains Mono'";
                ctxCanvas.fillText(`${price.toFixed(price < 1 ? 4 : 2)}`, w - 90, sy + 3);
            });

            // 2. Bids (Buyers / Support Pools Below Mark)
            orderbookBids.forEach((b, idx) => {
                const price = b[0];
                const size = b[1];
                const sy = h - ((price - pMin) / pRange) * (h - 80) - 40;
                const norm = Math.min(1.0, Math.log10(1 + size * 8) / Math.log10(1 + maxBookSize * 8));
                const bandH = Math.max(4, norm * 18);

                const grad = ctxCanvas.createLinearGradient(0, sy - bandH/2, 0, sy + bandH/2);
                grad.addColorStop(0, "rgba(0, 230, 118, 0)");
                if (norm > 0.6) {
                    grad.addColorStop(0.3, "rgba(255, 235, 0, 0.6)");
                    grad.addColorStop(0.5, "rgba(0, 240, 255, 0.95)"); // Bright Cyan Core
                    grad.addColorStop(0.7, "rgba(0, 230, 118, 0.6)");
                } else if (norm > 0.3) {
                    grad.addColorStop(0.5, "rgba(0, 230, 118, 0.6)"); // Emerald Green
                } else {
                    grad.addColorStop(0.5, "rgba(0, 180, 216, 0.35)"); // Cyan Base
                }
                grad.addColorStop(1, "rgba(0, 230, 118, 0)");

                ctxCanvas.fillStyle = grad;
                const bandWidth = w - 180;
                ctxCanvas.fillRect(20, sy - bandH/2, bandWidth, bandH);

                const barW = norm * 70;
                ctxCanvas.fillStyle = norm > 0.6 ? "rgba(0, 240, 255, 0.85)" : "rgba(0, 230, 118, 0.5)";
                ctxCanvas.fillRect(w - 170, sy - 2, barW, 4);

                ctxCanvas.fillStyle = "#cbd5e1";
                ctxCanvas.font = "9px 'JetBrains Mono'";
                ctxCanvas.fillText(`${price.toFixed(price < 1 ? 4 : 2)}`, w - 90, sy + 3);
            });

            // TOP 2 MEGA WHALE WALL ANNOTATIONS
            if (orderbookAsks.length > 0) {
                const topAsk = orderbookAsks.reduce((max, a) => a[1] > max[1] ? a : max, orderbookAsks[0]);
                const aY = h - ((topAsk[0] - pMin) / pRange) * (h - 80) - 40;

                ctxCanvas.strokeStyle = "#ff1744";
                ctxCanvas.setLineDash([4, 4]);
                ctxCanvas.beginPath();
                ctxCanvas.moveTo(20, aY);
                ctxCanvas.lineTo(w - 180, aY);
                ctxCanvas.stroke();
                ctxCanvas.setLineDash([]);

                ctxCanvas.fillStyle = "rgba(255, 23, 68, 0.25)";
                ctxCanvas.strokeStyle = "#ff1744";
                ctxCanvas.lineWidth = 1;
                ctxCanvas.fillRect(24, aY - 20, 280, 20);
                ctxCanvas.strokeRect(24, aY - 20, 280, 20);

                ctxCanvas.fillStyle = "#ff80ab";
                ctxCanvas.font = "bold 10px 'JetBrains Mono'";
                ctxCanvas.fillText(`⚡ MAJOR ASK RESISTANCE: $${topAsk[0].toFixed(1)} (${topAsk[1].toFixed(2)} Vol)`, 30, aY - 6);
            }

            if (orderbookBids.length > 0) {
                const topBid = orderbookBids.reduce((max, b) => b[1] > max[1] ? b : max, orderbookBids[0]);
                const bY = h - ((topBid[0] - pMin) / pRange) * (h - 80) - 40;

                ctxCanvas.strokeStyle = "#00e676";
                ctxCanvas.setLineDash([4, 4]);
                ctxCanvas.beginPath();
                ctxCanvas.moveTo(20, bY);
                ctxCanvas.lineTo(w - 180, bY);
                ctxCanvas.stroke();
                ctxCanvas.setLineDash([]);

                ctxCanvas.fillStyle = "rgba(0, 230, 118, 0.25)";
                ctxCanvas.strokeStyle = "#00e676";
                ctxCanvas.lineWidth = 1;
                ctxCanvas.fillRect(24, bY + 4, 280, 20);
                ctxCanvas.strokeRect(24, bY + 4, 280, 20);

                ctxCanvas.fillStyle = "#b9f6ca";
                ctxCanvas.font = "bold 10px 'JetBrains Mono'";
                ctxCanvas.fillText(`⚡ INSTITUTIONAL BEDROCK: $${topBid[0].toFixed(1)} (${topBid[1].toFixed(2)} Vol)`, 30, bY + 18);
            }

            // LIVE MARK PRICE LASER BEAM
            const curY = h - ((lastMarkPrice - pMin) / pRange) * (h - 80) - 40;
            ctxCanvas.strokeStyle = "#00f0ff";
            ctxCanvas.lineWidth = 2;
            ctxCanvas.beginPath();
            ctxCanvas.moveTo(0, curY);
            ctxCanvas.lineTo(w - 175, curY);
            ctxCanvas.stroke();

            // Pulsating Leading Dot
            ctxCanvas.fillStyle = "#00f0ff";
            ctxCanvas.beginPath();
            ctxCanvas.arc(w - 175, curY, 4, 0, Math.PI * 2);
            ctxCanvas.fill();

            // Right Price Badge
            ctxCanvas.fillStyle = "#00f0ff";
            ctxCanvas.fillRect(w - 85, curY - 10, 78, 20);
            ctxCanvas.fillStyle = "#000000";
            ctxCanvas.font = "bold 10px 'JetBrains Mono'";
            ctxCanvas.fillText(`$${lastMarkPrice.toFixed(lastMarkPrice < 1 ? 4 : 2)}`, w - 80, curY + 4);
        }

        """
    content = content[:old_func_start] + new_heatmap_code + content[old_func_end:]
    with open("static/pro_charts.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Enhanced heatmap engine replaced in static/pro_charts.html!")
else:
    print("ERROR: Function boundaries not found!")
