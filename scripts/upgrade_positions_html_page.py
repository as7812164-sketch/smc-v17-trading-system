import re

with open("static/positions.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update Bitget CSS in positions.html
pos_css = """        /* =========================================================
           BITGET PRO OFFICIAL POSITION CARD (+25% SCALED)
           ========================================================= */
        .bitget-pos-card {
            background: #0E131D;
            border: 1px solid rgba(255, 255, 255, 0.09);
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.55);
            border-radius: 12px;
            padding: 18px 16px;
            margin-bottom: 16px;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
            position: relative;
        }

        .bpc-header-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
            width: 100%;
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
        }

        .bpc-icon-btn {
            background: transparent;
            border: none;
            color: #848E9C;
            font-size: 16px;
            cursor: pointer;
            padding: 4px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .bpc-icon-btn:hover { color: #FFFFFF; }

        .bpc-badges-row {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 14px;
        }

        .bpc-badge-short {
            background: rgba(246, 70, 93, 0.18);
            color: #F6465D;
            border: 1px solid rgba(246, 70, 93, 0.35);
            font-size: 13px;
            font-weight: 800;
            padding: 2.5px 7px;
            border-radius: 4px;
        }

        .bpc-badge-long {
            background: rgba(14, 203, 129, 0.18);
            color: #0ECB81;
            border: 1px solid rgba(14, 203, 129, 0.35);
            font-size: 13px;
            font-weight: 800;
            padding: 2.5px 7px;
            border-radius: 4px;
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
        }

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
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .bpc-pnl-val {
            font-size: 26px;
            font-weight: 900;
            font-family: 'JetBrains Mono', monospace;
            font-variant-numeric: tabular-nums;
            display: flex;
            align-items: baseline;
            gap: 6px;
        }
        .bpc-pnl-val.green { color: #00F59B; text-shadow: 0 0 16px rgba(0, 245, 155, 0.25); }
        .bpc-pnl-val.red { color: #FF4D6A; text-shadow: 0 0 16px rgba(255, 77, 106, 0.25); }

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
        }
        .bpc-grid-col.left { align-items: flex-start; text-align: left; }
        .bpc-grid-col.center { align-items: flex-start; text-align: left; }
        .bpc-grid-col.right { align-items: flex-end; text-align: right; }

        .bpc-grid-lbl {
            font-size: 13.5px;
            color: #848E9C;
            font-weight: 600;
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
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .amber-highlight {
            color: #F59E0B !important;
            font-weight: 900 !important;
        }

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
        .bpc-levels-lbl { color: #848E9C; font-weight: 600; }
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
        }

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
        }
        .bpc-btn:active { transform: scale(0.97); background: rgba(255, 255, 255, 0.15); }
        .bpc-btn.close-btn {
            background: rgba(246, 70, 93, 0.12);
            color: #F6465D;
            border-color: rgba(246, 70, 93, 0.25);
        }
"""

css_start = html.find(".bitget-pos-card {")
css_end = html.find("/* =========================================================\n           DRAWER / SIDEBAR", css_start)
if css_start != -1 and css_end != -1:
    html = html[:css_start] + pos_css + "\n\n        " + html[css_end:]
    print("Updated positions.html CSS!")

# 2. Update Card Template in positions.html
idx_card = html.find("return `\n                    <div class=\"bitget-pos-card\" id=\"card-${pos.id}\">")
if idx_card != -1:
    idx_end = html.find("</div>\n                    `;\n            }).join('');", idx_card)
    if idx_end != -1:
        new_template = """const pnl = Number(pos.unrealized_pnl || 0);
                const isPos = pnl >= 0;
                const pnlColor = isPos ? 'green' : 'red';
                const sign = isPos ? '+' : '';
                const sideRaw = (pos.side_raw || pos.side || 'BUY').toUpperCase();
                const isBuy = sideRaw === 'BUY' || sideRaw === 'LONG';
                const sideText = isBuy ? 'Long' : 'Short';
                const sideBadgeClass = isBuy ? 'bpc-badge-long' : 'bpc-badge-short';
                const pnlFormatted = Math.abs(pnl).toFixed(4);
                const pnlApproxVal = Math.abs(pnl) < 0.01 ? '< $0.01' : `≈ $${Math.abs(pnl).toFixed(2)}`;
                const roeVal = Number(pos.pnl_pct || pos.roi_pct || 0);
                const roeFormatted = `${sign}${roeVal.toFixed(2)}%`;

                const entryPrice = Number(pos.entry_price || 0).toFixed(4);
                const markPrice = Number(pos.mark_price || pos.current_price || entryPrice).toFixed(4);
                const liqPrice = (pos.liq_price && pos.liq_price !== '--') ? Number(pos.liq_price).toFixed(4) : (
                    isBuy ? (Number(pos.entry_price) * 0.8125).toFixed(4) : (Number(pos.entry_price) * 1.1875).toFixed(4)
                );
                const coinName = pos.coin_name || (pos.symbol || '').replace('USDT', '');
                const sizeUsdt = Number(pos.size_usdt || pos.position_size_usdt || 25).toFixed(1);
                const sizeCoin = pos.size_coin ? Number(pos.size_coin).toFixed(pos.size_coin >= 10 ? 0 : 2) : (Number(pos.entry_price) > 0 ? (sizeUsdt / Number(pos.entry_price)).toFixed(0) : '0');
                const marginVal = Number(pos.margin_usdt || 4.9938).toFixed(4);
                const mmrVal = pos.mmr || '5.30%';
                const realizedPnl = Number(pos.realized_pnl || -0.0050);
                const realizedPnlStr = pos.realized_pnl_str || `${realizedPnl >= 0 ? '+' : ''}${realizedPnl.toFixed(4)}`;

                const tpVal = pos.tp_price ? Number(pos.tp_price).toFixed(4) : (isBuy ? (entryPrice * 1.03).toFixed(4) : (entryPrice * 0.97).toFixed(4));
                const slVal = pos.sl_price ? Number(pos.sl_price).toFixed(4) : (isBuy ? (entryPrice * 0.985).toFixed(4) : (entryPrice * 1.015).toFixed(4));

                const currentDrawdown = roeVal < 0 ? Math.abs(roeVal) : 0;
                const maeVal = Math.max(Number(pos.mae_pct || 0), currentDrawdown).toFixed(2);
                const mfeVal = Math.max(Number(pos.mfe_pct || 0), Math.max(0, roeVal)).toFixed(2);
                const durationStr = pos.duration_str || pos.duration || 'Live';

                return `
                    <div class="bitget-pos-card" id="card-${pos.id}">
                        <!-- Row 1: Symbol & Header Icons (Bitget Exact) -->
                        <div class="bpc-header-top">
                            <div class="bpc-symbol-wrap" onclick="window.location.href='/?symbol=${pos.symbol}'">
                                <span class="bpc-symbol">${pos.symbol}</span>
                                <i class="fa-solid fa-chevron-right bpc-sym-arrow"></i>
                            </div>
                            <div class="bpc-header-icons">
                                <button class="bpc-icon-btn" title="AI Sentinel Shield" style="color:#00F59B;"><i class="fa-solid fa-wand-magic-sparkles"></i></button>
                                <button class="bpc-icon-btn" title="View Full Chart" onclick="window.location.href='/?symbol=${pos.symbol}'"><i class="fa-solid fa-chart-candlestick"></i></button>
                                <button class="bpc-icon-btn" title="Share PnL Card" onclick="sharePosition('${pos.symbol}', '${sideText}', '${pnlFormatted}', '${roeFormatted}')"><i class="fa-solid fa-share-nodes"></i></button>
                            </div>
                        </div>

                        <!-- Row 2: Badges (Short, 5x, Isolated, USDT) -->
                        <div class="bpc-badges-row">
                            <span class="${sideBadgeClass}">${sideText}</span>
                            <span class="bpc-pill-outline">${pos.leverage || '5x'} <i class="fa-solid fa-pen" style="font-size:9px; opacity:0.7;"></i></span>
                            <span class="bpc-pill-outline">${pos.margin_mode || 'Isolated'}</span>
                            <span class="bpc-pill-outline">USDT</span>
                        </div>

                        <!-- Row 3: Unrealized PnL & ROE -->
                        <div class="bpc-pnl-row">
                            <div class="bpc-pnl-group">
                                <span class="bpc-sublabel">Unrealized PnL (USDT) <i class="fa-solid fa-circle-info" style="font-size:11px; color:#64748B;"></i></span>
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
                                <span class="bpc-grid-lbl">Size (${coinName}) <i class="fa-solid fa-caret-down" style="font-size:10px;"></i></span>
                                <span class="bpc-grid-val">${sizeCoin}</span>
                            </div>
                            <div class="bpc-grid-col center">
                                <span class="bpc-grid-lbl">Margin (USDT)</span>
                                <span class="bpc-grid-val">${marginVal} <i class="fa-solid fa-circle-plus" style="font-size:12px; color:#848E9C;"></i></span>
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
                                    <i class="fa-solid fa-pen" style="font-size:10px; opacity:0.7;"></i>
                                </span>
                            </div>
                            <div class="bpc-levels-row">
                                <span class="bpc-levels-lbl">Partial TP/SL</span>
                                <span class="bpc-levels-val">
                                    TP 0 / SL 1 <i class="fa-solid fa-pen" style="font-size:10px; opacity:0.7;"></i>
                                </span>
                            </div>
                        </div>

                        <!-- Row 7: Hermes Quant Armor Strip -->
                        <div class="bpc-armor-strip">
                            <span>MAE: <b style="color:#FF4D6A;">-${maeVal}%</b></span>
                            <span>MFE: <b style="color:#00F59B;">+${mfeVal}%</b></span>
                            <span>Duration: <b>${durationStr}</b></span>
                            <span style="background:rgba(0,245,155,0.15); color:#00F59B; padding:2px 6px; border-radius:4px; font-weight:800;"><i class="fa-solid fa-shield-halved"></i> Model 2A</span>
                        </div>

                        <!-- Row 8: 3-Button Action Dock (Bitget Pro Exact) -->
                        <div class="bpc-dock">
                            <button class="bpc-btn" onclick="alert('Take Profit: $' + '${tpVal}' + ' | Stop Loss: $' + '${slVal}')">TP/SL</button>
                            <button class="bpc-btn" onclick="alert('Reverse position on ${pos.symbol} at next 50% Mean Threshold confirmation.')">Reverse</button>
                            <button class="bpc-btn close-btn" onclick="closePosition(${pos.id}, '${pos.symbol}')">Close</button>
                        </div>
                    </div>
                `;"""
        # Find where map starts
        idx_map = html.rfind("const mfe =", 0, idx_card)
        if idx_map != -1:
            html = html[:idx_map] + new_template + html[idx_end + len("</div>\n                    `;"):]
            print("Updated positions.html card template successfully!")

with open("static/positions.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Saved updated static/positions.html!")
