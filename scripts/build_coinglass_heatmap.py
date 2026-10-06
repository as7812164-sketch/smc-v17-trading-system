import re

with open("static/pro_charts.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's inspect pro_charts.html and insert the CoinGlass control bar and renderer
coinglass_styles = """
        /* COINGLASS HEATMAP STYLES */
        .cg-controls-bar {
            position: absolute;
            top: 8px;
            left: 12px;
            right: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(11, 16, 26, 0.85);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(51, 65, 85, 0.6);
            border-radius: 8px;
            padding: 5px 12px;
            z-index: 60;
            font-family: var(--font-mono);
            font-size: 11px;
        }

        .cg-left-controls {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .cg-pill-group {
            display: flex;
            background: rgba(18, 24, 38, 0.8);
            border: 1px solid rgba(51, 65, 85, 0.5);
            border-radius: 6px;
            padding: 2px;
            gap: 2px;
        }

        .cg-pill {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.15s;
        }

        .cg-pill:hover { color: #fff; }
        .cg-pill.active {
            background: rgba(0, 240, 255, 0.2);
            color: var(--cyan-glow);
        }

        .cg-legend {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 10px;
            color: var(--text-muted);
        }

        .cg-legend-bar {
            width: 140px;
            height: 8px;
            border-radius: 4px;
            background: linear-gradient(90deg, #0d1b2a, #00f0ff, #00e676, #ffd700, #ff0054);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
"""

# Insert coinglass styles into <style>
if ".cg-controls-bar" not in html:
    html = html.replace("</style>", coinglass_styles + "\n    </style>")

# Insert coinglass controls bar into heatmap-stage
cg_controls_html = """
                        <!-- COINGLASS TOP CONTROLS & LEGEND BAR -->
                        <div class="cg-controls-bar" id="cgControlsBar">
                            <div class="cg-left-controls">
                                <span style="font-weight:800; color:var(--cyan-glow);"><i class="fa-solid fa-chart-area"></i> COINGLASS HEATMAP</span>
                                <div class="cg-pill-group">
                                    <button class="cg-pill active" onclick="setCoinglassRange('24h')">24H</button>
                                    <button class="cg-pill" onclick="setCoinglassRange('3d')">3D</button>
                                    <button class="cg-pill" onclick="setCoinglassRange('7d')">7D</button>
                                    <button class="cg-pill" onclick="setCoinglassRange('30d')">30D</button>
                                </div>
                                <div class="cg-pill-group">
                                    <button class="cg-pill active" onclick="setCoinglassLev('all')">All Lev</button>
                                    <button class="cg-pill" onclick="setCoinglassLev('100x')">100x</button>
                                    <button class="cg-pill" onclick="setCoinglassLev('50x')">50x</button>
                                    <button class="cg-pill" onclick="setCoinglassLev('25x')">25x</button>
                                </div>
                            </div>
                            <div class="cg-legend">
                                <span>Low ($0M)</span>
                                <div class="cg-legend-bar"></div>
                                <span style="color:#ff80ab; font-weight:700;">Nuclear ($500M+)</span>
                            </div>
                        </div>
"""

if "id=\"cgControlsBar\"" not in html:
    html = html.replace("<div class=\"heatmap-stage\">", "<div class=\"heatmap-stage\">\n" + cg_controls_html)

with open("static/pro_charts.html", "w", encoding="utf-8") as f:
    f.write(html)

print("SUCCESS: Inserted CoinGlass Controls & Legend into static/pro_charts.html!")
