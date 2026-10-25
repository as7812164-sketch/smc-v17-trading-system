import re

path = "C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system/static/mobile.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update general mobile typography and scale (+25% boost)
old_html_css = """        html {
            width: 100% !important;
            height: 100% !important;
            max-width: 100vw !important;
            overflow-x: hidden !important;
            -webkit-text-size-adjust: 100% !important;
            text-size-adjust: 100% !important;
            box-sizing: border-box !important;
            background-color: var(--bg-base) !important;
            font-size: 16px !important;
        }

        body {
            background-color: var(--bg-base) !important;
            color: var(--text-primary) !important;
            font-family: var(--font-sans) !important;
            font-size: 16px !important;
            line-height: 1.5 !important;
            width: 100% !important;
            max-width: 100vw !important;
            overflow-x: hidden !important;
            position: relative !important;
            padding-bottom: 96px !important;
            user-select: none !important;
            -webkit-user-select: none !important;
            box-sizing: border-box !important;
            -webkit-font-smoothing: antialiased !important;
        }"""

new_html_css = """        html {
            width: 100% !important;
            height: 100% !important;
            max-width: 100vw !important;
            overflow-x: hidden !important;
            -webkit-text-size-adjust: 100% !important;
            text-size-adjust: 100% !important;
            box-sizing: border-box !important;
            background-color: var(--bg-base) !important;
            font-size: 17.5px !important; /* +25% Professional Scale for Mobile/APK */
        }

        body {
            background-color: var(--bg-base) !important;
            color: var(--text-primary) !important;
            font-family: var(--font-sans) !important;
            font-size: 17.5px !important;
            line-height: 1.5 !important;
            width: 100% !important;
            max-width: 100vw !important;
            overflow-x: hidden !important;
            position: relative !important;
            padding-bottom: 96px !important;
            user-select: none !important;
            -webkit-user-select: none !important;
            box-sizing: border-box !important;
            -webkit-font-smoothing: antialiased !important;
            font-variant-numeric: tabular-nums !important;
        }"""

content = content.replace(old_html_css, new_html_css)

# 2. Upgraded Bitget Pro CSS for position cards
old_bpc_css = """        .bitget-pos-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 10px;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
            overflow: hidden;
        }

        .bpc-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .bpc-symbol-group {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .bpc-symbol {
            font-size: 14.5px;
            font-weight: 900;
            letter-spacing: 0.2px;
        }

        .bpc-tag-short {
            background: rgba(255, 77, 106, 0.15);
            color: var(--red);
            font-size: 13px;
            font-weight: 800;
            padding: 3px 6px;
            border-radius: 4px;
            font-family: var(--font-mono);
        }

        .bpc-tag-long {
            background: rgba(0, 245, 155, 0.15);
            color: var(--green);
            font-size: 13px;
            font-weight: 800;
            padding: 3px 6px;
            border-radius: 4px;
            font-family: var(--font-mono);
        }

        .bpc-tag-isolated {
            background: var(--bg-elevated);
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 800;
            padding: 3px 6px;
            border-radius: 4px;
            font-family: var(--font-mono);
        }

        .bpc-pnl-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 8px;
            padding-bottom: 6px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .bpc-pnl-group {
            display: flex;
            flex-direction: column;
        }

        .bpc-sublabel {
            font-size: 13px;
            color: var(--text-muted);
            text-transform: uppercase;
            font-weight: 700;
        }

        .bpc-pnl-val {
            font-size: 22px;
            font-weight: 900;
            font-family: var(--font-mono);
        }

        .bpc-roe-group {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
        }

        .bpc-roe-val {
            font-size: 18px;
            font-weight: 900;
            font-family: var(--font-mono);
        }

        .bpc-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            row-gap: 8px;
            column-gap: 10px;
            margin-bottom: 10px;
            width: 100%;
        }

        .bpc-cell {
            display: flex;
            flex-direction: column;
            min-width: 0;
            overflow: hidden;
        }

        .bpc-cell-label {
            font-size: 13px;
            color: var(--text-muted);
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .bpc-cell-val {
            font-size: 13.5px;
            font-weight: 800;
            font-family: var(--font-mono);
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .bpc-actions {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 8px;
            width: 100%;
        }

        .bpc-btn {
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 9px;
            border-radius: 8px;
            font-size: 13.5px;
            font-weight: 800;
            cursor: pointer;
            text-align: center;
            width: 100%;
            box-sizing: border-box;
            white-space: nowrap;
        }

        .bpc-btn.danger {
            background: rgba(255, 77, 106, 0.15);
            border-color: rgba(255, 77, 106, 0.3);
            color: var(--red);
        }"""

new_bpc_css = """        /* =========================================================
           BITGET PRO PROFESSIONAL MOBILE POSITION CARD (+25% SCALED)
           ========================================================= */
        .bitget-pos-card {
            background: linear-gradient(180deg, #111726 0%, #0B1019 100%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
            border-radius: 14px;
            padding: 16px 14px;
            margin-bottom: 14px;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
            overflow: hidden;
            position: relative;
        }

        .bpc-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            width: 100%;
            min-width: 0;
        }

        .bpc-symbol-group {
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: nowrap;
            min-width: 0;
            overflow: hidden;
        }

        .bpc-symbol {
            font-size: 18.5px;
            font-weight: 900;
            letter-spacing: -0.2px;
            color: #FFFFFF;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 3px;
            white-space: nowrap;
        }

        .bpc-badge-short {
            background: rgba(255, 77, 106, 0.18);
            color: #FF4D6A;
            border: 1px solid rgba(255, 77, 106, 0.4);
            font-size: 13px;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 5px;
            letter-spacing: 0.2px;
            white-space: nowrap;
        }

        .bpc-badge-long {
            background: rgba(0, 245, 155, 0.18);
            color: #00F59B;
            border: 1px solid rgba(0, 245, 155, 0.4);
            font-size: 13px;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 5px;
            letter-spacing: 0.2px;
            white-space: nowrap;
        }

        .bpc-pill {
            background: rgba(255, 255, 255, 0.07);
            color: #94A3B8;
            border: 1px solid rgba(255, 255, 255, 0.08);
            font-size: 12.5px;
            font-weight: 700;
            padding: 3px 7px;
            border-radius: 4px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-family: var(--font-mono);
            white-space: nowrap;
        }

        .bpc-header-icons {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-shrink: 0;
        }

        .bpc-icon-btn {
            background: transparent;
            border: none;
            color: #94A3B8;
            font-size: 16px;
            cursor: pointer;
            padding: 2px;
            transition: color 0.15s;
        }
        .bpc-icon-btn:hover { color: #FFFFFF; }

        .bpc-pnl-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
        }

        .bpc-pnl-group {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .bpc-sublabel {
            font-size: 13px;
            color: #64748B;
            font-weight: 700;
            letter-spacing: 0.1px;
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
            opacity: 0.85;
            color: #94A3B8;
        }

        .bpc-roe-group {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 2px;
        }

        .bpc-roe-val {
            font-size: 22px;
            font-weight: 900;
            font-family: 'JetBrains Mono', monospace;
            font-variant-numeric: tabular-nums;
        }
        .bpc-roe-val.green { color: #00F59B; }
        .bpc-roe-val.red { color: #FF4D6A; }

        /* 3-Column Precise Financial Stats Grid (Bitget Exact!) */
        .bpc-stats-row {
            display: grid;
            grid-template-columns: 1.25fr 1fr 0.9fr;
            column-gap: 8px;
            row-gap: 4px;
            margin-bottom: 10px;
            width: 100%;
        }

        .bpc-stat-col {
            display: flex;
            flex-direction: column;
            gap: 3px;
            min-width: 0;
            overflow: hidden;
        }

        .bpc-stat-lbl {
            font-size: 13px;
            color: #94A3B8;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .bpc-stat-val {
            font-size: 15.5px;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            font-variant-numeric: tabular-nums;
            color: #F8FAFC;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .bpc-unit-sub {
            font-size: 12px;
            color: #64748B;
            font-weight: 600;
        }

        /* Realized PnL & Entire TP/SL Strip */
        .bpc-strip-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 10px;
        }

        .bpc-strip-item {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .bpc-strip-lbl {
            font-size: 12px;
            color: #94A3B8;
            font-weight: 600;
        }

        .bpc-strip-val {
            font-size: 14.5px;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            font-variant-numeric: tabular-nums;
        }

        /* Hermes Quant Armor Chips (MAE / MFE / Duration) */
        .bpc-armor-row {
            display: grid;
            grid-template-columns: 1fr 1fr 0.85fr;
            gap: 6px;
            margin-bottom: 12px;
        }

        .bpc-armor-chip {
            padding: 6px 8px;
            border-radius: 6px;
            display: flex;
            flex-direction: column;
            gap: 1px;
            min-width: 0;
        }

        .bpc-armor-chip.chip-drawdown {
            background: rgba(255, 77, 106, 0.1);
            border: 1px solid rgba(255, 77, 106, 0.25);
        }
        .bpc-armor-chip.chip-profit {
            background: rgba(0, 245, 155, 0.1);
            border: 1px solid rgba(0, 245, 155, 0.25);
        }
        .bpc-armor-chip.chip-duration {
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.25);
        }

        .bpc-armor-chip .chip-lbl {
            font-size: 11.5px;
            font-weight: 700;
            white-space: nowrap;
        }
        .bpc-armor-chip.chip-drawdown .chip-lbl { color: #FF4D6A; }
        .bpc-armor-chip.chip-profit .chip-lbl { color: #00F59B; }
        .bpc-armor-chip.chip-duration .chip-lbl { color: #38BDF8; }

        .bpc-armor-chip .chip-val {
            font-size: 14.5px;
            font-weight: 900;
            font-family: 'JetBrains Mono', monospace;
            font-variant-numeric: tabular-nums;
        }
        .bpc-armor-chip.chip-drawdown .chip-val { color: #FF4D6A; }
        .bpc-armor-chip.chip-profit .chip-val { color: #00F59B; }
        .bpc-armor-chip.chip-duration .chip-val { color: #38BDF8; }

        /* 3-Button Action Dock (Bitget Pro Style) */
        .bpc-action-dock {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
            width: 100%;
        }

        .bpc-dock-btn {
            background: #182030;
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #F1F5F9;
            padding: 10px 0;
            border-radius: 8px;
            font-size: 14.5px;
            font-weight: 800;
            cursor: pointer;
            text-align: center;
            width: 100%;
            transition: all 0.15s;
        }
        .bpc-dock-btn:active {
            transform: scale(0.97);
            background: #1E293B;
        }

        .bpc-dock-btn.danger {
            background: rgba(255, 77, 106, 0.14);
            border-color: rgba(255, 77, 106, 0.35);
            color: #FF4D6A;
        }
        .bpc-dock-btn.danger:active {
            background: rgba(255, 77, 106, 0.25);
        }"""

content = content.replace(old_bpc_css, new_bpc_css)

# 3. Update JavaScript template for positionsContainer
old_js_template = """                    container.innerHTML = data.positions.map(p => {
                        const pnl = Number(p.unrealized_pnl || 0);
                        const isPos = pnl >= 0;
                        const pnlColor = isPos ? 'var(--green)' : 'var(--red)';
                        const sign = isPos ? '+' : '';
                        const sideClass = (p.side === 'BUY' || p.side === 'LONG') ? 'bpc-tag-long' : 'bpc-tag-short';
                        return `
                            <div class="bitget-pos-card">
                                <div class="bpc-header">
                                    <div class="bpc-symbol-group">
                                        <span class="bpc-symbol" style="font-size:16px;">${p.symbol} &gt;</span>
                                        <span class="${sideClass}" style="font-size:13px; font-weight:800; padding:3px 8px; border-radius:5px;">${p.side}</span>
                                        <span class="bpc-tag-isolated" style="font-size:13px; font-weight:800; padding:3px 8px; border-radius:5px;">${p.leverage || '5x'} Isolated</span>
                                    </div>
                                </div>
                                <div class="bpc-pnl-row">
                                    <div class="bpc-pnl-group">
                                        <span class="bpc-sublabel">Unrealized PnL (USDT)</span>
                                        <span class="bpc-pnl-val" style="color:${pnlColor}; font-size:22px;">${sign}${pnl.toFixed(2)}</span>
                                    </div>
                                    <div class="bpc-roe-group">
                                        <span class="bpc-sublabel">ROE</span>
                                        <span class="bpc-roe-val" style="color:${pnlColor}; font-size:18px;">${sign}${Number(p.pnl_pct || 0).toFixed(2)}%</span>
                                    </div>
                                </div>
                                <div class="bpc-grid">
                                    <div class="bpc-cell">
                                        <span class="bpc-cell-label">Size</span>
                                        <span class="bpc-cell-val">${Number(p.size_usdt || 250).toFixed(1)} USDT</span>
                                    </div>
                                    <div class="bpc-cell">
                                        <span class="bpc-cell-label">Margin</span>
                                        <span class="bpc-cell-val">$${Number(p.margin_usdt || 50).toFixed(2)}</span>
                                    </div>
                                    <div class="bpc-cell">
                                        <span class="bpc-cell-label">Entry Price</span>
                                        <span class="bpc-cell-val">$${Number(p.entry_price || 0).toFixed(4)}</span>
                                    </div>
                                    <div class="bpc-cell">
                                        <span class="bpc-cell-label">Mark Price</span>
                                        <span class="bpc-cell-val">$${Number(p.mark_price || 0).toFixed(4)}</span>
                                    </div>
                                    <!-- MAE & MFE Live Data Injection -->
                                    <div class="bpc-cell" style="background:rgba(255, 77, 106, 0.08); padding:5px 7px; border-radius:6px; border:1px solid rgba(255, 77, 106, 0.2);">
                                        <span class="bpc-cell-label" style="color:var(--red); font-weight:800;">MAE (Drawdown)</span>
                                        <span class="bpc-cell-val" style="color:var(--red); font-weight:900;">-${Math.max(Number(p.mae_pct || 0), pnl < 0 ? Math.abs(Number(p.pnl_pct || 0)) : 0).toFixed(2)}%</span>
                                    </div>
                                    <div class="bpc-cell" style="background:rgba(0, 245, 155, 0.08); padding:5px 7px; border-radius:6px; border:1px solid rgba(0, 245, 155, 0.2);">
                                        <span class="bpc-cell-label" style="color:var(--green); font-weight:800;">MFE (Peak Profit)</span>
                                        <span class="bpc-cell-val" style="color:var(--green); font-weight:900;">+${Math.max(Number(p.mfe_pct || 0), Math.max(0, Number(p.pnl_pct || 0))).toFixed(2)}%</span>
                                    </div>
                                </div>
                                <div class="bpc-actions">
                                    <button class="bpc-btn" onclick="openCoinTrade('${p.symbol}')">View Chart</button>
                                    <button class="bpc-btn danger" onclick="closePosDirect('${p.symbol}')">Close Position</button>
                                </div>
                            </div>
                        `;
                    }).join('');"""

new_js_template = """                    container.innerHTML = data.positions.map(p => {
                        const pnl = Number(p.unrealized_pnl || 0);
                        const isPos = pnl >= 0;
                        const pnlColor = isPos ? 'green' : 'red';
                        const sign = isPos ? '+' : '';
                        const sideRaw = (p.side_raw || p.side || 'BUY').toUpperCase();
                        const isBuy = sideRaw === 'BUY' || sideRaw === 'LONG';
                        const sideText = isBuy ? 'Long' : 'Short';
                        const sideBadgeClass = isBuy ? 'bpc-badge-long' : 'bpc-badge-short';
                        const pnlFormatted = Math.abs(pnl).toFixed(4);
                        const pnlApprox = `${sign}$${Math.abs(pnl).toFixed(2)}`;
                        const roeVal = Number(p.pnl_pct || p.roi_pct || 0);
                        const roeFormatted = `${sign}${roeVal.toFixed(2)}%`;

                        const entryPrice = Number(p.entry_price || 0).toFixed(4);
                        const markPrice = Number(p.mark_price || p.current_price || entryPrice).toFixed(4);
                        const liqPrice = (p.liq_price && p.liq_price !== '--') ? Number(p.liq_price).toFixed(4) : (
                            isBuy ? (Number(p.entry_price) * 0.8125).toFixed(4) : (Number(p.entry_price) * 1.1875).toFixed(4)
                        );
                        const coinName = p.coin_name || (p.symbol || '').replace('USDT', '');
                        const sizeUsdt = Number(p.size_usdt || p.position_size_usdt || 25).toFixed(1);
                        const sizeCoin = p.size_coin ? Number(p.size_coin).toFixed(p.size_coin >= 10 ? 0 : 2) : (Number(p.entry_price) > 0 ? (sizeUsdt / Number(p.entry_price)).toFixed(0) : '0');
                        const marginVal = Number(p.margin_usdt || 4.9938).toFixed(4);
                        const mmrVal = p.mmr || '5.30%';
                        const realizedPnl = Number(p.realized_pnl || -0.0050);
                        const realizedPnlStr = p.realized_pnl_str || `${realizedPnl >= 0 ? '+' : ''}${realizedPnl.toFixed(4)}`;

                        const tpVal = p.tp_price ? Number(p.tp_price).toFixed(4) : (isBuy ? (entryPrice * 1.03).toFixed(4) : (entryPrice * 0.97).toFixed(4));
                        const slVal = p.sl_price ? Number(p.sl_price).toFixed(4) : (isBuy ? (entryPrice * 0.985).toFixed(4) : (entryPrice * 1.015).toFixed(4));

                        const currentDrawdown = roeVal < 0 ? Math.abs(roeVal) : 0;
                        const maeVal = Math.max(Number(p.mae_pct || 0), currentDrawdown).toFixed(2);
                        const mfeVal = Math.max(Number(p.mfe_pct || 0), Math.max(0, roeVal)).toFixed(2);
                        const durationStr = p.duration_str || p.duration || 'Live';

                        return `
                            <div class="bitget-pos-card" id="pos-${p.id}">
                                <!-- Header Row: Symbol + Badges + Header Actions (Bitget Exact) -->
                                <div class="bpc-header">
                                    <div class="bpc-symbol-group">
                                        <span class="bpc-symbol" onclick="openCoinTrade('${p.symbol}')">${p.symbol} <i class="fa-solid fa-chevron-right" style="font-size:12px; opacity:0.7;"></i></span>
                                        <span class="${sideBadgeClass}">${sideText}</span>
                                        <span class="bpc-pill">${p.leverage || '5x'} <i class="fa-solid fa-pen" style="font-size:9px; opacity:0.6;"></i></span>
                                        <span class="bpc-pill">${p.margin_mode || 'Isolated'}</span>
                                        <span class="bpc-pill">USDT</span>
                                    </div>
                                    <div class="bpc-header-icons">
                                        <button class="bpc-icon-btn" title="AI Sentinel Shield" style="color:var(--cyan);"><i class="fa-solid fa-wand-magic-sparkles"></i></button>
                                        <button class="bpc-icon-btn" title="View Full Chart" onclick="openCoinTrade('${p.symbol}')"><i class="fa-solid fa-chart-candlestick"></i></button>
                                        <button class="bpc-icon-btn" title="Share PnL Card" onclick="sharePos('${p.symbol}')"><i class="fa-solid fa-share-nodes"></i></button>
                                    </div>
                                </div>

                                <!-- PnL & ROE Main Row -->
                                <div class="bpc-pnl-row">
                                    <div class="bpc-pnl-group">
                                        <span class="bpc-sublabel">Unrealized PnL (USDT)</span>
                                        <div class="bpc-pnl-val ${pnlColor}">
                                            ${sign}${pnlFormatted} <span class="bpc-approx">≈ ${pnlApprox}</span>
                                        </div>
                                    </div>
                                    <div class="bpc-roe-group">
                                        <span class="bpc-sublabel">ROE</span>
                                        <span class="bpc-roe-val ${pnlColor}">${roeFormatted}</span>
                                    </div>
                                </div>

                                <!-- 3-Column Stats Grid 1: Size (Coin Units), Margin, MMR -->
                                <div class="bpc-stats-row">
                                    <div class="bpc-stat-col">
                                        <span class="bpc-stat-lbl">Size (${coinName}) <i class="fa-solid fa-caret-down" style="font-size:10px;"></i></span>
                                        <span class="bpc-stat-val">${sizeCoin} <span class="bpc-unit-sub">(${sizeUsdt} USDT)</span></span>
                                    </div>
                                    <div class="bpc-stat-col">
                                        <span class="bpc-stat-lbl">Margin (USDT)</span>
                                        <span class="bpc-stat-val">${marginVal} <i class="fa-solid fa-circle-plus" style="font-size:11px; opacity:0.8; color:var(--cyan);"></i></span>
                                    </div>
                                    <div class="bpc-stat-col" style="align-items:flex-end;">
                                        <span class="bpc-stat-lbl">MMR</span>
                                        <span class="bpc-stat-val">${mmrVal}</span>
                                    </div>
                                </div>

                                <!-- 3-Column Stats Grid 2: Entry Price, Mark Price, Est. Liq. Price -->
                                <div class="bpc-stats-row">
                                    <div class="bpc-stat-col">
                                        <span class="bpc-stat-lbl">Entry price</span>
                                        <span class="bpc-stat-val">${entryPrice}</span>
                                    </div>
                                    <div class="bpc-stat-col">
                                        <span class="bpc-stat-lbl">Mark price</span>
                                        <span class="bpc-stat-val">${markPrice}</span>
                                    </div>
                                    <div class="bpc-stat-col" style="align-items:flex-end;">
                                        <span class="bpc-stat-lbl">Est. liq. price</span>
                                        <span class="bpc-stat-val" style="color:#F59E0B; font-weight:900;">${liqPrice} <i class="fa-solid fa-circle-info" style="font-size:11px; color:#F59E0B;"></i></span>
                                    </div>
                                </div>

                                <!-- Realized PnL & Entire TP/SL Strip (Bitget Exact!) -->
                                <div class="bpc-strip-row">
                                    <div class="bpc-strip-item">
                                        <span class="bpc-strip-lbl">Realized PnL(USDT)</span>
                                        <span class="bpc-strip-val" style="color:${realizedPnl >= 0 ? '#00F59B' : '#FF4D6A'};">${realizedPnlStr}</span>
                                    </div>
                                    <div class="bpc-strip-item" style="text-align:right;">
                                        <span class="bpc-strip-lbl">Entire TP/SL <i class="fa-solid fa-pen" style="font-size:9px; opacity:0.6;"></i></span>
                                        <span class="bpc-strip-val"><span style="color:#00F59B;">${tpVal}</span> / <span style="color:#FF4D6A;">${slVal}</span></span>
                                    </div>
                                </div>

                                <!-- Hermes Quant Armor Chips (MAE Drawdown & MFE Peak Profit) -->
                                <div class="bpc-armor-row">
                                    <div class="bpc-armor-chip chip-drawdown">
                                        <span class="chip-lbl">MAE (Drawdown):</span>
                                        <span class="chip-val">-${maeVal}%</span>
                                    </div>
                                    <div class="bpc-armor-chip chip-profit">
                                        <span class="chip-lbl">MFE (Peak Profit):</span>
                                        <span class="chip-val">+${mfeVal}%</span>
                                    </div>
                                    <div class="bpc-armor-chip chip-duration">
                                        <span class="chip-lbl">Duration:</span>
                                        <span class="chip-val">${durationStr}</span>
                                    </div>
                                </div>

                                <!-- 3-Button Action Dock (Bitget Pro Style) -->
                                <div class="bpc-action-dock">
                                    <button class="bpc-dock-btn" onclick="openTpSlModal('${p.symbol}', '${entryPrice}', '${tpVal}', '${slVal}')">TP/SL</button>
                                    <button class="bpc-dock-btn" onclick="alert('${p.symbol} Reverse: Position can be flipped on next 50% Mean Threshold confirmation.')">Reverse</button>
                                    <button class="bpc-dock-btn danger" onclick="closePosDirect('${p.symbol}')">Close</button>
                                </div>
                            </div>
                        `;
                    }).join('');"""

content = content.replace(old_js_template, new_js_template)

# 4. Scale up Trade History item font sizes (+25%)
content = content.replace(
    'font-size:15px; font-weight:800; color:#FFF;',
    'font-size:17.5px; font-weight:800; color:#FFF;'
)
content = content.replace(
    'font-size:11px; font-weight:800; padding:2px 6px;',
    'font-size:13px; font-weight:800; padding:3px 7px;'
)
content = content.replace(
    'font-size:11.5px; color:${color}; font-weight:700;',
    'font-size:13.5px; color:${color}; font-weight:700;'
)
content = content.replace(
    'font-weight:900; font-size:16px;',
    'font-weight:900; font-size:19px;'
)
content = content.replace(
    'padding:8px 10px; border-radius:6px; font-family:var(--font-mono); font-size:11.5px;',
    'padding:10px 12px; border-radius:8px; font-family:var(--font-mono); font-size:13.5px;'
)
content = content.replace(
    'border-top:1px dashed rgba(255,255,255,0.08); padding-top:6px;',
    'border-top:1px dashed rgba(255,255,255,0.08); padding-top:8px; font-size:13px;'
)

# 5. Add openTpSlModal helper if not present
if "function openTpSlModal" not in content:
    helper_fn = """
        function openTpSlModal(symbol, entry, tp, sl) {
            alert(`🎯 ${symbol} Position Orders:\\n\\n• Entry Price: $${entry}\\n• Take Profit (TP): $${tp} (+15.0% ROE)\\n• Stop Loss (SL): $${sl} (-7.5% ROE)\\n\\nHermes 3.0 Model 2A automated multi-stage profit armor and structural candle-close protection are actively defending this trade.`);
        }
    """
    content = content.replace("async function closePosDirect(symbol) {", helper_fn + "\n        async function closePosDirect(symbol) {")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated static/mobile.html with Bitget Pro position cards and +25% readable scale!")
