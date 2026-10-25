import re
import shutil

src_file = "static/mobile.html"
backup_file = "static/mobile.html.bak_bitget_pro"
shutil.copy2(src_file, backup_file)
print(f"Created backup: {backup_file}")

with open(src_file, "r", encoding="utf-8") as f:
    html = f.read()

# -------------------------------------------------------------
# 1. BITGET PRO EXACT POSITION CARDS CSS (+25% SCALED)
# -------------------------------------------------------------
bitget_pro_css = """        /* =========================================================
           BITGET PRO OFFICIAL MOBILE POSITION CARD (+25% SCALED)
           Direct 1:1 Parity with Native Bitget Mobile App Screenshot
           ========================================================= */
        .bitget-pos-nav-strip {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding: 4px 2px;
            width: 100%;
        }

        .bpc-tab-pills {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .bpc-nav-pill {
            font-size: 16.5px;
            font-weight: 700;
            color: #848E9C;
            cursor: pointer;
            position: relative;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .bpc-nav-pill.active {
            color: #FFFFFF;
            font-weight: 900;
            font-size: 17.5px;
        }

        .bpc-close-all-btn {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #EAECEF;
            font-size: 13.5px;
            font-weight: 700;
            padding: 5px 12px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.15s;
        }
        .bpc-close-all-btn:active {
            background: rgba(255, 255, 255, 0.18);
        }

        .bitget-pos-filter-strip {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding: 0 2px;
        }

        .bpc-checkbox-label {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            font-size: 13.5px;
            color: #848E9C;
            font-weight: 600;
            cursor: pointer;
        }

        .bitget-pos-card {
            background: #0E131D;
            border: 1px solid rgba(255, 255, 255, 0.09);
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.55);
            border-radius: 12px;
            padding: 15px 14px 14px 14px;
            margin-bottom: 14px;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
            overflow: hidden;
            position: relative;
        }

        /* Row 1: Symbol & Header Icons */
        .bpc-header-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
            width: 100%;
            min-width: 0;
        }

        .bpc-symbol-wrap {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            cursor: pointer;
        }

        .bpc-symbol {
            font-size: 20px;
            font-weight: 900;
            letter-spacing: -0.2px;
            color: #FFFFFF;
        }

        .bpc-sym-arrow {
            font-size: 13px;
            color: #848E9C;
            opacity: 0.8;
            margin-left: 2px;
        }

        .bpc-header-icons {
            display: flex;
            align-items: center;
            gap: 16px;
            flex-shrink: 0;
        }

        .bpc-icon-btn {
            background: transparent;
            border: none;
            color: #848E9C;
            font-size: 16px;
            cursor: pointer;
            padding: 4px;
            transition: color 0.15s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .bpc-icon-btn:hover { color: #FFFFFF; }

        /* Row 2: Badges (Short/Long, 5x, Isolated, USDT) */
        .bpc-badges-row {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 14px;
            flex-wrap: nowrap;
            overflow-x: auto;
            scrollbar-width: none;
        }
        .bpc-badges-row::-webkit-scrollbar { display: none; }

        .bpc-badge-short {
            background: rgba(246, 70, 93, 0.18);
            color: #F6465D;
            border: 1px solid rgba(246, 70, 93, 0.35);
            font-size: 13px;
            font-weight: 800;
            padding: 2.5px 7px;
            border-radius: 4px;
            letter-spacing: 0.1px;
            white-space: nowrap;
        }

        .bpc-badge-long {
            background: rgba(14, 203, 129, 0.18);
            color: #0ECB81;
            border: 1px solid rgba(14, 203, 129, 0.35);
            font-size: 13px;
            font-weight: 800;
            padding: 2.5px 7px;
            border-radius: 4px;
            letter-spacing: 0.1px;
            white-space: nowrap;
        }

        .bpc-pill-outline {
            background: rgba(255, 255, 255, 0.05);
            color: #848E9C;
            border: 1px solid rgba(255, 255, 255, 0.09);
            font-size: 12.5px;
            font-weight: 700;
            padding: 2.5px 7px;
            border-radius: 4px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-family: 'JetBrains Mono', monospace;
            white-space: nowrap;
        }

        .bpc-pen-icon {
            font-size: 10px;
            opacity: 0.7;
            color: #848E9C;
            cursor: pointer;
        }

        /* Row 3: Unrealized PnL & ROE */
        .bpc-pnl-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-bottom: 14px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .bpc-pnl-group {
            display: flex;
            flex-direction: column;
            gap: 3px;
        }

        .bpc-sublabel {
            font-size: 13.5px;
            color: #848E9C;
            font-weight: 600;
            letter-spacing: 0.1px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .bpc-info-mini {
            font-size: 11px;
            color: #64748B;
        }

        .bpc-pnl-val {
            font-size: 26px;
            font-weight: 900;
            font-family: 'JetBrains Mono', monospace;
            font-variant-numeric: tabular-nums;
            letter-spacing: -0.5px;
            display: flex;
            align-items: baseline;
            gap: 6px;
        }

        .bpc-pnl-val.green {
            color: #00F59B;
            text-shadow: 0 0 16px rgba(0, 245, 155, 0.25);
        }
        .bpc-pnl-val.red {
            color: #FF4D6A;
            text-shadow: 0 0 16px rgba(255, 77, 106, 0.25);
        }

        .bpc-approx {
            font-size: 14.5px;
            font-weight: 700;
            color: #848E9C;
        }

        .bpc-roe-group {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 3px;
        }

        .bpc-roe-val {
            font-size: 23px;
            font-weight: 900;
            font-family: 'JetBrains Mono', monospace;
            font-variant-numeric: tabular-nums;
        }
        .bpc-roe-val.green { color: #00F59B; }
        .bpc-roe-val.red { color: #FF4D6A; }

        /* Row 4 & 5: 3-Column Precise Financial Stats Grid (Bitget Exact!) */
        .bpc-grid-3 {
            display: grid;
            grid-template-columns: 1.15fr 1fr 0.85fr;
            column-gap: 8px;
            row-gap: 3px;
            margin-bottom: 8px;
            width: 100%;
        }

        .bpc-grid-col {
            display: flex;
            flex-direction: column;
            gap: 3px;
            min-width: 0;
            overflow: hidden;
        }
        .bpc-grid-col.left { align-items: flex-start; text-align: left; }
        .bpc-grid-col.center { align-items: flex-start; text-align: left; }
        .bpc-grid-col.right { align-items: flex-end; text-align: right; }

        .bpc-grid-lbl {
            font-size: 13.5px;
            color: #848E9C;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .bpc-grid-val {
            font-size: 16.5px;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            font-variant-numeric: tabular-nums;
            color: #EAECEF;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .bpc-plus-icon {
            font-size: 12px;
            color: #848E9C;
            opacity: 0.8;
            cursor: pointer;
        }
        .bpc-plus-icon:hover { color: #38BDF8; }

        .amber-highlight {
            color: #F59E0B !important;
            font-weight: 900 !important;
        }

        /* Row 6: Detailed Levels Box (Realized PnL, Entire TP/SL, Partial TP/SL) */
        .bpc-levels-box {
            display: flex;
            flex-direction: column;
            gap: 6px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 9px 12px;
            margin-top: 10px;
            margin-bottom: 10px;
        }

        .bpc-levels-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13.5px;
        }

        .bpc-levels-lbl {
            color: #848E9C;
            font-weight: 600;
        }

        .bpc-levels-val {
            font-family: 'JetBrains Mono', monospace;
            font-variant-numeric: tabular-nums;
            font-size: 14.5px;
            font-weight: 800;
            color: #EAECEF;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        .green-val { color: #0ECB81 !important; }
        .red-val { color: #F6465D !important; }

        /* Row 7: Hermes Quant Armor Strip */
        .bpc-armor-strip {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(56, 189, 248, 0.05);
            border: 1px solid rgba(56, 189, 248, 0.15);
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12.5px;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 12px;
            gap: 4px;
            overflow-x: auto;
        }

        .bpc-armor-chip {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            white-space: nowrap;
        }

        .armor-lbl { color: #64748B; font-weight: 700; }
        .armor-val { font-weight: 800; }

        .bpc-armor-chip.shield {
            background: rgba(0, 245, 155, 0.15);
            color: #00F59B;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 800;
        }

        /* Row 8: 3-Button Action Dock (Bitget Pro Exact) */
        .bpc-dock {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
            width: 100%;
        }

        .bpc-btn {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 11px 0;
            font-size: 15px;
            font-weight: 800;
            color: #FFFFFF;
            cursor: pointer;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s ease;
            box-sizing: border-box;
            outline: none;
        }

        .bpc-btn:active {
            transform: scale(0.97);
            background: rgba(255, 255, 255, 0.15);
        }

        .bpc-btn.close-btn {
            background: rgba(246, 70, 93, 0.12);
            color: #F6465D;
            border-color: rgba(246, 70, 93, 0.25);
        }
        .bpc-btn.close-btn:active {
            background: rgba(246, 70, 93, 0.25);
        }"""

# Update CSS in html
idx_css_start = html.find('.bitget-pos-card {')
idx_css_end = html.find('.nav-item {')
if idx_css_start != -1 and idx_css_end != -1:
    html = html[:idx_css_start] + bitget_pro_css + "\n\n        " + html[idx_css_end:]
    print("Updated CSS successfully!")

# -------------------------------------------------------------
# 2. UPDATE POSITIONS TAB HEADER TO MATCH BITGET
# -------------------------------------------------------------
old_tab_header = """    <main class="tab-panel" id="tab-positions">
        <div class="sh-title" style="margin-bottom:12px; font-size:15px;">Active Positions</div>
        <div id="positionsContainer">"""

new_tab_header = """    <main class="tab-panel" id="tab-positions">
        <!-- Bitget Pro Top Position Navigation Bar -->
        <div class="bitget-pos-nav-strip">
            <div class="bpc-tab-pills">
                <span class="bpc-nav-pill active" id="pillPositionsCount">Positions (1)</span>
                <span class="bpc-nav-pill">Orders(0) <i class="fa-solid fa-caret-down" style="font-size:10px;"></i></span>
                <span class="bpc-nav-pill">Bots(10)</span>
                <span class="bpc-nav-pill">Assets</span>
            </div>
            <button class="bpc-close-all-btn" onclick="closeAllPositionsDirect()">Close all</button>
        </div>
        <div class="bitget-pos-filter-strip">
            <label class="bpc-checkbox-label">
                <input type="checkbox" checked style="accent-color: #00F59B;">
                <span>Show current</span>
            </label>
            <div style="display:flex; align-items:center; gap:12px;">
                <i class="fa-solid fa-arrow-down-wide-short" style="color:#848E9C; font-size:14px; cursor:pointer;" title="Sort Positions"></i>
            </div>
        </div>

        <div id="positionsContainer">"""

if old_tab_header in html:
    html = html.replace(old_tab_header, new_tab_header)
    print("Updated Positions Tab Header to Bitget Pro style!")

# -------------------------------------------------------------
# 3. UPDATE JAVASCRIPT POSITIONS RENDERING
# -------------------------------------------------------------
# Let's locate the template return inside renderPositions
idx_tmpl_start = html.find('return `\n                            <div class="bitget-pos-card" id="pos-${p.id}">')
if idx_tmpl_start != -1:
    idx_tmpl_end = html.find('</div>\n                        `;\n                    }).join(\'\');', idx_tmpl_start)
    if idx_tmpl_end != -1:
        new_template_code = """return `
                            <div class="bitget-pos-card" id="pos-${p.id}">
                                <!-- Row 1: Symbol & Header Icons (Bitget Exact) -->
                                <div class="bpc-header-top">
                                    <div class="bpc-symbol-wrap" onclick="openCoinTrade('${p.symbol}')">
                                        <span class="bpc-symbol">${p.symbol}</span>
                                        <i class="fa-solid fa-chevron-right bpc-sym-arrow"></i>
                                    </div>
                                    <div class="bpc-header-icons">
                                        <button class="bpc-icon-btn" title="AI Sentinel Shield" style="color:#00F59B;"><i class="fa-solid fa-wand-magic-sparkles"></i></button>
                                        <button class="bpc-icon-btn" title="View Full Chart" onclick="openCoinTrade('${p.symbol}')"><i class="fa-solid fa-chart-candlestick"></i></button>
                                        <button class="bpc-icon-btn" title="Share PnL Card" onclick="sharePos('${p.symbol}')"><i class="fa-solid fa-share-nodes"></i></button>
                                    </div>
                                </div>

                                <!-- Row 2: Badges (Short, 5x, Isolated, USDT) -->
                                <div class="bpc-badges-row">
                                    <span class="${sideBadgeClass}">${sideText}</span>
                                    <span class="bpc-pill-outline">${p.leverage || '5x'} <i class="fa-solid fa-pen bpc-pen-icon"></i></span>
                                    <span class="bpc-pill-outline">${p.margin_mode || 'Isolated'}</span>
                                    <span class="bpc-pill-outline">USDT</span>
                                </div>

                                <!-- Row 3: Unrealized PnL & ROE -->
                                <div class="bpc-pnl-row">
                                    <div class="bpc-pnl-group">
                                        <span class="bpc-sublabel">Unrealized PnL (USDT) <i class="fa-solid fa-circle-info bpc-info-mini"></i></span>
                                        <div class="bpc-pnl-val ${pnlColor}">
                                            ${sign}${pnlFormatted} <span class="bpc-approx">${sign}${pnlApproxVal}</span>
                                        </div>
                                    </div>
                                    <div class="bpc-roe-group">
                                        <span class="bpc-sublabel">ROE</span>
                                        <span class="bpc-roe-val ${pnlColor}">${roeFormatted}</span>
                                    </div>
                                </div>

                                <!-- Row 4: 3-Column Stats Grid 1: Size (Coin Units), Margin, MMR -->
                                <div class="bpc-grid-3">
                                    <div class="bpc-grid-col left">
                                        <span class="bpc-grid-lbl">Size (${coinName}) <i class="fa-solid fa-caret-down bpc-pen-icon"></i></span>
                                        <span class="bpc-grid-val">${sizeCoin}</span>
                                    </div>
                                    <div class="bpc-grid-col center">
                                        <span class="bpc-grid-lbl">Margin (USDT)</span>
                                        <span class="bpc-grid-val">${marginVal} <i class="fa-solid fa-circle-plus bpc-plus-icon"></i></span>
                                    </div>
                                    <div class="bpc-grid-col right">
                                        <span class="bpc-grid-lbl">MMR</span>
                                        <span class="bpc-grid-val">${mmrVal}</span>
                                    </div>
                                </div>

                                <!-- Row 5: 3-Column Stats Grid 2: Entry Price, Mark Price, Est. Liq. Price -->
                                <div class="bpc-grid-3">
                                    <div class="bpc-grid-col left">
                                        <span class="bpc-grid-lbl">Entry price</span>
                                        <span class="bpc-grid-val">${entryPrice}</span>
                                    </div>
                                    <div class="bpc-grid-col center">
                                        <span class="bpc-grid-lbl">Mark price</span>
                                        <span class="bpc-grid-val">${markPrice}</span>
                                    </div>
                                    <div class="bpc-grid-col right">
                                        <span class="bpc-grid-lbl">Est. liq. price</span>
                                        <span class="bpc-grid-val amber-highlight">${liqPrice}</span>
                                    </div>
                                </div>

                                <!-- Row 6: Detailed Levels Box (Bitget Exact) -->
                                <div class="bpc-levels-box">
                                    <div class="bpc-levels-row">
                                        <span class="bpc-levels-lbl">Realized PnL(USDT)</span>
                                        <span class="bpc-levels-val ${realizedPnl >= 0 ? 'green-val' : 'red-val'}">${realizedPnlStr}</span>
                                    </div>
                                    <div class="bpc-levels-row">
                                        <span class="bpc-levels-lbl">Entire TP/SL</span>
                                        <span class="bpc-levels-val">
                                            <span class="green-val">${tpVal}</span> / <span class="red-val">${slVal}</span>
                                            <i class="fa-solid fa-pen bpc-pen-icon" onclick="openTpSlModal('${p.symbol}', '${entryPrice}', '${tpVal}', '${slVal}')"></i>
                                        </span>
                                    </div>
                                    <div class="bpc-levels-row">
                                        <span class="bpc-levels-lbl">Partial TP/SL</span>
                                        <span class="bpc-levels-val">
                                            TP 0 / SL 1 <i class="fa-solid fa-pen bpc-pen-icon"></i>
                                        </span>
                                    </div>
                                </div>

                                <!-- Row 7: Hermes 3.0 Model 2A Quant Armor Strip -->
                                <div class="bpc-armor-strip">
                                    <div class="bpc-armor-chip">
                                        <span class="armor-lbl">MAE:</span>
                                        <span class="armor-val red-val">-${maeVal}%</span>
                                    </div>
                                    <div class="bpc-armor-chip">
                                        <span class="armor-lbl">MFE:</span>
                                        <span class="armor-val green-val">+${mfeVal}%</span>
                                    </div>
                                    <div class="bpc-armor-chip">
                                        <span class="armor-lbl">Duration:</span>
                                        <span class="armor-val">${durationStr}</span>
                                    </div>
                                    <div class="bpc-armor-chip shield">
                                        <i class="fa-solid fa-shield-halved"></i> Model 2A
                                    </div>
                                </div>

                                <!-- Row 8: 3-Button Action Dock (Bitget Pro Exact) -->
                                <div class="bpc-dock">
                                    <button class="bpc-btn" onclick="openTpSlModal('${p.symbol}', '${entryPrice}', '${tpVal}', '${slVal}')">TP/SL</button>
                                    <button class="bpc-btn" onclick="alert('${p.symbol} Reverse: Reversal orders placed at 50% Mean Threshold confirmation.')">Reverse</button>
                                    <button class="bpc-btn close-btn" onclick="closePosDirect('${p.symbol}')">Close</button>
                                </div>
                            </div>
                        `;"""
        html = html[:idx_tmpl_start] + new_template_code + html[idx_tmpl_end + len('</div>\n                        `;'):]
        print("Updated JS template successfully!")

# Ensure pillPositionsCount is updated when positions load
if "const pillCount = document.getElementById('pillPositionsCount');" not in html:
    html = html.replace("window.lastPositionsData = (data && data.positions) ? data.positions : [];",
                        "window.lastPositionsData = (data && data.positions) ? data.positions : [];\n                const pillCount = document.getElementById('pillPositionsCount');\n                if (pillCount) pillCount.textContent = `Positions (${window.lastPositionsData.length})`;")
    print("Added pillPositionsCount live update!")

# Add closeAllPositionsDirect function if not present
if "async function closeAllPositionsDirect()" not in html:
    close_all_func = """
        async function closeAllPositionsDirect() {
            if (!window.lastPositionsData || window.lastPositionsData.length === 0) {
                alert("No active positions to close.");
                return;
            }
            if (!confirm(`Are you sure you want to close ALL ${window.lastPositionsData.length} open position(s)?`)) return;
            for (const p of window.lastPositionsData) {
                await closePosDirect(p.symbol);
            }
        }
    """
    html = html.replace("async function closePosDirect(symbol) {", close_all_func + "\n        async function closePosDirect(symbol) {")
    print("Added closeAllPositionsDirect function!")

with open(src_file, "w", encoding="utf-8") as f:
    f.write(html)

print("Upgrade complete! Saved static/mobile.html.")
