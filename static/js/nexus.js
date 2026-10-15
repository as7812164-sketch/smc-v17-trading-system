/**
 * NEXUSPRO CLIENT ENGINE (100% BITGET PRO UX)
 * ===========================================
 * - Lightweight Charts (Candlesticks + Timeframes)
 * - Live Order Book Depth Streamer
 * - Order Placement Desk (5x-100x Isolated Leverage)
 * - Bottom Dock (Positions, History, Deca Allocations)
 * - Mobile Drawer & Top Ticker Bar
 */

let currentSymbol = "BTCUSDT";
let currentInterval = "15m";
let currentLeverage = 5;
let chart = null;
let candleSeries = null;

// Parse symbol from URL (e.g. /trade?symbol=SOLUSDT)
const urlParams = new URLSearchParams(window.location.search);
const symParam = urlParams.get('symbol');
if (symParam) currentSymbol = symParam.toUpperCase();

const ALL_CHAMPIONS = [
    { s: "BTCUSDT", sec: 1 }, { s: "ETHUSDT", sec: 1 },
    { s: "SOLUSDT", sec: 2 }, { s: "BNBUSDT", sec: 2 },
    { s: "AVAXUSDT", sec: 3 }, { s: "DOGEUSDT", sec: 3 },
    { s: "DOTUSDT", sec: 4 }, { s: "LINKUSDT", sec: 4 },
    { s: "LTCUSDT", sec: 5 }, { s: "NEARUSDT", sec: 5 },
    { s: "OPUSDT", sec: 6 }, { s: "RENDERUSDT", sec: 6 },
    { s: "SUIUSDT", sec: 7 }, { s: "TIAUSDT", sec: 7 },
    { s: "UNIUSDT", sec: 8 }, { s: "XRPUSDT", sec: 8 },
    { s: "1000PEPEUSDT", sec: 9 }, { s: "APTUSDT", sec: 9 },
    { s: "ARBUSDT", sec: 10 }, { s: "FETUSDT", sec: 10 }
];

function renderPairModalList(filter = "") {
    const listEl = document.getElementById("pairModalList");
    if (!listEl) return;
    const q = filter.toUpperCase();
    const filtered = ALL_CHAMPIONS.filter(x => x.s.includes(q));
    listEl.innerHTML = filtered.map(x => `
        <div onclick="selectPair('${x.s}')" style="display:flex; justify-content:space-between; align-items:center; padding:10px 12px; border-radius:6px; cursor:pointer; margin-bottom:4px; background:var(--bg-base); border:1px solid var(--border-subtle); transition:border-color 0.2s;">
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-weight:800; color:#fff; font-size:13px;">${x.s}</span>
                <span style="font-size:9px; background:var(--bg-surface-elevated); padding:2px 4px; border-radius:3px; color:var(--text-muted);">PERP</span>
            </div>
            <span style="font-size:10px; font-weight:800; color:var(--brand-teal);">Section ${x.sec}</span>
        </div>
    `).join("");
}

function filterPairModal(q) {
    renderPairModalList(q);
}

function selectPair(sym) {
    changePair(sym);
    const modal = document.getElementById("pairModal");
    if (modal) modal.style.display = "none";
}

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
    const symEl = document.getElementById("displayPairSymbol");
    if (symEl) symEl.innerText = currentSymbol;
    renderPairModalList();
    initChart();
    loadKlines();
    startDataPollers();
    setupOrderDesk();
});

// ----------------- LIGHTWEIGHT CHART -----------------

function initChart() {
    const container = document.getElementById("tradingview_chart");
    if (!container || !window.LightweightCharts) return;

    chart = LightweightCharts.createChart(container, {
        layout: {
            background: { color: '#0F1420' },
            textColor: '#94A3B8',
            fontSize: 11,
            fontFamily: "'JetBrains Mono', monospace"
        },
        grid: {
            vertLines: { color: 'rgba(255, 255, 255, 0.04)' },
            horzLines: { color: 'rgba(255, 255, 255, 0.04)' }
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: 'rgba(255, 255, 255, 0.08)',
        },
        timeScale: {
            borderColor: 'rgba(255, 255, 255, 0.08)',
            timeVisible: true,
            secondsVisible: false,
        }
    });

    candleSeries = chart.addCandlestickSeries({
        upColor: '#00C087',
        downColor: '#FF4B55',
        borderVisible: false,
        wickUpColor: '#00C087',
        wickDownColor: '#FF4B55'
    });

    window.addEventListener('resize', () => {
        if (chart && container) {
            chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
        }
    });
}

async function loadKlines() {
    if (!candleSeries) return;
    try {
        const res = await fetch(`/api/klines/${currentSymbol}?interval=${currentInterval}&limit=120`);
        const data = await res.json();
        if (data.candles && data.candles.length > 0) {
            candleSeries.setData(data.candles);
            if (chart) chart.timeScale().fitContent();
        }
    } catch (e) {
        console.error("Failed to load klines:", e);
    }
}

function setTimeframe(tf, btn) {
    currentInterval = tf;
    document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    loadKlines();
}

function changePair(sym) {
    currentSymbol = sym.toUpperCase();
    const symEl = document.getElementById("displayPairSymbol");
    if (symEl) symEl.innerText = currentSymbol;
    loadKlines();
    pollTicker();
    pollOrderBook();
}

// ----------------- LIVE DATA POLLERS -----------------

function startDataPollers() {
    pollTicker();
    pollHeaderBtcEthTicker();
    pollOrderBook();
    pollPositions();
    pollTradeHistory();
    pollSummary();
    pollDockRadar();
    pollSentries();

    setInterval(pollTicker, 2500);
    setInterval(pollHeaderBtcEthTicker, 3000);
    setInterval(pollOrderBook, 2500);
    setInterval(pollPositions, 3000);
    setInterval(pollTradeHistory, 4000);
    setInterval(pollSummary, 5000);
    setInterval(pollDockRadar, 6000);
    setInterval(pollSentries, 10000);
}

async function pollHeaderBtcEthTicker() {
    try {
        const resBtc = await fetch('/api/ticker/BTCUSDT');
        if (resBtc.ok) {
            const btc = await resBtc.json();
            const btcPriceEl = document.getElementById("navBtcPrice");
            const btcChgEl = document.getElementById("navBtcChg");
            if (btcPriceEl && btc.last_price > 0) {
                btcPriceEl.innerText = `$${btc.last_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            }
            if (btcChgEl) {
                const sign = btc.price_change_pct >= 0 ? '+' : '';
                btcChgEl.innerText = `${sign}${btc.price_change_pct.toFixed(2)}%`;
                btcChgEl.className = `pair-change-pill ${btc.price_change_pct >= 0 ? 'pill-green' : 'pill-red'}`;
            }
        }
        const resEth = await fetch('/api/ticker/ETHUSDT');
        if (resEth.ok) {
            const eth = await resEth.json();
            const ethPriceEl = document.getElementById("navEthPrice");
            const ethChgEl = document.getElementById("navEthChg");
            if (ethPriceEl && eth.last_price > 0) {
                ethPriceEl.innerText = `$${eth.last_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            }
            if (ethChgEl) {
                const sign = eth.price_change_pct >= 0 ? '+' : '';
                ethChgEl.innerText = `${sign}${eth.price_change_pct.toFixed(2)}%`;
                ethChgEl.className = `pair-change-pill ${eth.price_change_pct >= 0 ? 'pill-green' : 'pill-red'}`;
            }
        }
    } catch (e) {}
}

async function pollTicker() {
    try {
        const res = await fetch(`/api/ticker/${currentSymbol}`);
        if (!res.ok) return;
        const t = await res.json();

        const pEl = document.getElementById("displayPrice");
        const chEl = document.getElementById("displayChangePill");
        const highEl = document.getElementById("displayHigh24");
        const lowEl = document.getElementById("displayLow24");
        const volEl = document.getElementById("displayVol24");
        const orderPriceInput = document.getElementById("inputPrice");

        if (pEl && t.last_price > 0) {
            pEl.innerText = t.last_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 });
            pEl.style.color = t.price_change_pct >= 0 ? 'var(--buy-green)' : 'var(--sell-red)';
        }
        if (chEl) {
            const sign = t.price_change_pct >= 0 ? '+' : '';
            chEl.innerText = `${sign}${t.price_change_pct.toFixed(2)}%`;
            chEl.className = `pair-change-pill ${t.price_change_pct >= 0 ? 'pill-green' : 'pill-red'}`;
        }
        if (highEl) highEl.innerText = t.high_24h.toLocaleString();
        if (lowEl) lowEl.innerText = t.low_24h.toLocaleString();
        if (volEl) volEl.innerText = `${(t.volume_24h / 1e6).toFixed(2)}M`;

        if (orderPriceInput && !orderPriceInput.dataset.manual && t.last_price > 0) {
            orderPriceInput.value = t.last_price;
        }

        // Live chart tick update
        if (candleSeries && t.last_price > 0) {
            candleSeries.update({
                time: Math.floor(Date.now() / 1000),
                open: t.last_price,
                high: t.last_price,
                low: t.last_price,
                close: t.last_price
            });
        }
    } catch (e) {
        console.error("Ticker poll error:", e);
    }
}

async function pollOrderBook() {
    try {
        const res = await fetch(`/api/orderbook/${currentSymbol}?depth=8`);
        if (!res.ok) return;
        const ob = await res.json();

        const asksContainer = document.getElementById("obAsks");
        const bidsContainer = document.getElementById("obBids");
        const midPriceEl = document.getElementById("obMidPrice");

        if (asksContainer && ob.asks) {
            let asksHtml = "";
            const maxVol = Math.max(...ob.asks.map(a => a[1]), 1.0);
            ob.asks.slice().reverse().forEach(([p, q]) => {
                const widthPct = Math.min(100, (q / maxVol) * 100);
                asksHtml += `
                    <div class="ob-row" onclick="fillPrice(${p})">
                        <div class="ob-depth-bar ask" style="width:${widthPct}%"></div>
                        <span style="color:var(--sell-red)">${p.toFixed(4)}</span>
                        <span>${q.toFixed(2)}</span>
                    </div>
                `;
            });
            asksContainer.innerHTML = asksHtml;
        }

        if (midPriceEl && ob.asks && ob.asks.length > 0) {
            midPriceEl.innerText = ob.asks[0][0].toFixed(4);
        }

        if (bidsContainer && ob.bids) {
            let bidsHtml = "";
            const maxVol = Math.max(...ob.bids.map(b => b[1]), 1.0);
            ob.bids.forEach(([p, q]) => {
                const widthPct = Math.min(100, (q / maxVol) * 100);
                bidsHtml += `
                    <div class="ob-row" onclick="fillPrice(${p})">
                        <div class="ob-depth-bar bid" style="width:${widthPct}%"></div>
                        <span style="color:var(--buy-green)">${p.toFixed(4)}</span>
                        <span>${q.toFixed(2)}</span>
                    </div>
                `;
            });
            bidsContainer.innerHTML = bidsHtml;
        }
    } catch (e) {
        console.error("OrderBook poll error:", e);
    }
}

function fillPrice(price) {
    const input = document.getElementById("inputPrice");
    if (input) {
        input.value = price;
        input.dataset.manual = "true";
    }
}

// ----------------- PORTFOLIO SUMMARY -----------------

async function pollSummary() {
    try {
        const res = await fetch("/api/deca/summary");
        if (!res.ok) return;
        const s = await res.json();

        const eqEl = document.getElementById("topTotalEquity");
        const pnlEl = document.getElementById("topTotalPnl");
        const wrEl = document.getElementById("topWinRate");
        const capEl = document.getElementById("availMarginDesk");

        if (eqEl) eqEl.innerText = `$${s.total_equity.toFixed(2)}`;
        if (pnlEl) {
            const sign = s.total_pnl >= 0 ? '+' : '';
            pnlEl.innerText = `${sign}$${s.total_pnl.toFixed(2)} (${sign}${s.pnl_pct.toFixed(2)}%)`;
            pnlEl.className = `stat-val ${s.total_pnl >= 0 ? 'green' : 'pill-red'}`;
        }
        if (wrEl) wrEl.innerText = `${s.win_rate.toFixed(1)}% (${s.total_wins}W/${s.total_losses}L)`;
        if (capEl) {
            const free = s.free_margin !== undefined ? s.free_margin : (s.total_balance / 10);
            capEl.innerText = `$${free.toFixed(2)} USDT`;
        }
    } catch (e) {
        console.error("Summary poll error:", e);
    }
}

// ----------------- POSITIONS & BOTTOM DOCK -----------------

async function pollPositions() {
    try {
        const res = await fetch("/api/trade/positions");
        if (!res.ok) return;
        const data = await res.json();

        const tbody = document.getElementById("positionsTableBody");
        const countBadge = document.getElementById("posCountBadge");
        if (countBadge) countBadge.innerText = data.count;

        if (tbody) {
            if (!data.positions || data.positions.length === 0) {
                tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:var(--text-muted); padding:30px;">No Open Positions • BB 2.0 Autonomous Scanner Standing By</td></tr>`;
            } else {
                tbody.innerHTML = data.positions.map(p => {
                    const isLong = (p.side_raw || p.side || '').toUpperCase() === 'LONG' || (p.side_raw || p.side || '').toUpperCase() === 'BUY';
                    const sideStr = isLong ? 'LONG' : 'SHORT';
                    const lev = (p.leverage || '5x').toString().replace('x', '') + 'x';
                    const posSize = Number(p.position_size_usdt || p.size_usdt || 250.0);
                    const margin = Number(p.margin_usdt || (posSize / 5.0));
                    const roe = p.roi_pct !== undefined ? Number(p.roi_pct) : Number(p.pnl_pct || 0);
                    const uPnl = p.unrealized_pnl !== undefined ? Number(p.unrealized_pnl) : Number(p.unrealized_pnl_usdt || 0);
                    const sign = uPnl >= 0 ? '+' : '';
                    const pnlColor = uPnl >= 0 ? 'var(--buy-green)' : 'var(--sell-red)';
                    const secId = p.section_id || p.account_id || 1;
                    const entryP = Number(p.entry_price || 0);
                    const markP = Number(p.mark_price || p.current_price || entryP);
                    const slP = Number(p.trailing_sl_price > 0 ? p.trailing_sl_price : p.sl_price || 0);
                    const tpP = Number(p.tp_price || 0);

                    return `
                        <tr>
                            <td>
                                <span style="font-weight:800; color:#fff;">${p.symbol}</span>
                                <span style="font-size:10px; padding:2px 4px; border-radius:3px; background:${isLong ? 'rgba(0,192,135,0.15)' : 'rgba(255,75,85,0.15)'}; color:${isLong ? 'var(--buy-green)' : 'var(--sell-red)'}; font-weight:800; margin-left:4px;">${sideStr} ${lev}</span>
                                <span style="font-size:10px; color:var(--text-muted); margin-left:4px;">${p.timeframe || '4H'}</span>
                            </td>
                            <td><span style="color:var(--brand-teal); font-weight:700;">Section ${secId}</span></td>
                            <td style="font-family:var(--font-mono);">$${posSize.toFixed(2)} <span style="color:var(--text-muted); font-size:11px;">($${margin.toFixed(2)})</span></td>
                            <td style="font-family:var(--font-mono); font-weight:700;">${entryP.toFixed(4)}</td>
                            <td style="font-family:var(--font-mono);">${markP.toFixed(4)}</td>
                            <td style="font-family:var(--font-mono); color:${slP > entryP ? 'var(--buy-green)' : 'var(--sell-red)'}; font-weight:700;">${slP.toFixed(4)}</td>
                            <td style="font-family:var(--font-mono); color:var(--buy-green); font-weight:700;">${tpP.toFixed(4)}</td>
                            <td style="color:${pnlColor}; font-weight:800; font-family:var(--font-mono);">${sign}$${uPnl.toFixed(2)} (${sign}${roe.toFixed(2)}%)</td>
                            <td>
                                <button class="btn-close-pos" onclick="closePosition(${p.id})">Close</button>
                            </td>
                        </tr>
                    `;
                }).join("");
            }
        }
    } catch (e) {
        console.error("Positions poll error:", e);
    }
}

async function pollTradeHistory() {
    try {
        const res = await fetch("/api/trade/history?limit=30");
        if (!res.ok) return;
        const data = await res.json();
        const trades = data.trades || [];

        const tbody = document.getElementById("historyTableBody");
        const countBadge = document.getElementById("historyCountBadge");
        if (countBadge) countBadge.innerText = trades.length;

        if (tbody) {
            if (trades.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding:30px;">No Executed Trades Found</td></tr>`;
            } else {
                tbody.innerHTML = trades.map(t => {
                    const isLong = (t.side || "").toUpperCase() === "LONG" || (t.side || "").toUpperCase() === "BUY";
                    const pnl = Number(t.pnl_usdt || 0);
                    const isWin = pnl >= 0;
                    const sign = isWin ? "+" : "";
                    const pnlColor = isWin ? "var(--buy-green)" : "var(--sell-red)";
                    const roe = t.roi_pct !== undefined ? t.roi_pct : (t.pnl_pct || 0);
                    const exitReason = t.exit_reason || t.result || (isWin ? "TP Hit" : "SL Hit");
                    return `
                        <tr>
                            <td>
                                <span style="font-weight:800; color:#fff;">${t.symbol}</span>
                                <span style="font-size:10px; padding:2px 4px; border-radius:3px; background:${isLong ? 'rgba(0,192,135,0.15)' : 'rgba(255,75,85,0.15)'}; color:${isLong ? 'var(--buy-green)' : 'var(--sell-red)'}; font-weight:800; margin-left:4px;">${isLong ? 'LONG' : 'SHORT'}</span>
                            </td>
                            <td><span style="font-size:11px; color:var(--text-secondary);">${t.timeframe || '4H'}</span></td>
                            <td style="font-family:var(--font-mono);">${Number(t.entry_price || 0).toFixed(4)}</td>
                            <td style="font-family:var(--font-mono);">${Number(t.exit_price || t.entry_price || 0).toFixed(4)}</td>
                            <td style="color:${pnlColor}; font-weight:800; font-family:var(--font-mono);">${sign}$${pnl.toFixed(2)}</td>
                            <td style="color:${pnlColor}; font-weight:800; font-family:var(--font-mono);">${sign}${Number(roe).toFixed(2)}%</td>
                            <td>
                                <span style="font-size:10px; padding:2px 6px; border-radius:4px; font-weight:700; background:${isWin ? 'rgba(0,192,135,0.15)' : 'rgba(255,75,85,0.15)'}; color:${isWin ? 'var(--buy-green)' : 'var(--sell-red)'};">
                                    ${exitReason}
                                </span>
                            </td>
                            <td style="font-size:11px; color:var(--text-muted);">${t.exit_time_str || t.duration || t.duration_str || '--'}</td>
                        </tr>
                    `;
                }).join("");
            }
        }
    } catch (e) {
        console.error("Trade history poll error:", e);
    }
}

async function closePosition(posId) {
    if (!confirm(`Confirm close position #${posId}?`)) return;
    try {
        const res = await fetch(`/api/trade/close/${posId}`, { method: 'POST' });
        const resData = await res.json();
        pollPositions();
        pollSummary();
    } catch (e) {
        alert("Failed to close position: " + e);
    }
}

// ----------------- ORDER DESK EXECUTION -----------------

function setupOrderDesk() {
    const inputAmount = document.getElementById("inputAmount");
    document.querySelectorAll(".pct-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const pct = parseInt(btn.dataset.pct, 10);
            if (inputAmount) {
                // Base $50 section balance percentage
                inputAmount.value = ((50.0 * (pct / 100.0))).toFixed(1);
            }
        });
    });
}

async function placeOrder(side) {
    const inputPrice = document.getElementById("inputPrice");
    const inputAmount = document.getElementById("inputAmount");

    const marginUsdt = parseFloat(inputAmount ? inputAmount.value : 25) || 25.0;
    const entryPrice = parseFloat(inputPrice ? inputPrice.value : 0) || 0.0;

    const payload = {
        symbol: currentSymbol,
        side: side,
        order_type: "LIMIT",
        leverage: currentLeverage,
        margin_usdt: marginUsdt,
        entry_price: entryPrice
    };

    try {
        const res = await fetch("/api/trade/order", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === "SUCCESS") {
            alert(`⚡ Order Placed: ${side} ${currentSymbol} @ ${data.entry_price}`);
            pollPositions();
            pollSummary();
        } else {
            alert(`Order Error: ${JSON.stringify(data)}`);
        }
    } catch (e) {
        alert("Order submission failed: " + e);
    }
}

// ----------------- MOBILE DRAWER -----------------

function toggleDrawer() {
    const drawer = document.getElementById("mobileDrawer");
    const overlay = document.getElementById("mobileDrawerOverlay");
    if (!drawer || !overlay) return;

    if (drawer.classList.contains("open")) {
        drawer.classList.remove("open");
        overlay.style.display = "none";
    } else {
        drawer.classList.add("open");
        overlay.style.display = "block";
    }
}

// ----------------- DOCK TAB SWITCHER & HERMES INTEGRATIONS -----------------

function switchDockTab(tab) {
    const tabs = ['positions', 'history', 'radar', 'sentries', 'ai'];
    tabs.forEach(t => {
        const btn = document.getElementById('tabBtn' + t.charAt(0).toUpperCase() + t.slice(1));
        const pane = document.getElementById('dockPane' + t.charAt(0).toUpperCase() + t.slice(1));
        if (btn) btn.classList.toggle('active', t === tab);
        if (pane) pane.style.display = (t === tab) ? 'block' : 'none';
    });

    if (tab === 'positions') pollPositions();
    if (tab === 'history') pollTradeHistory();
    if (tab === 'radar') pollDockRadar();
    if (tab === 'sentries') pollSentries();
}

async function pollDockRadar() {
    const tbody = document.getElementById("dockRadarTableBody");
    const badge = document.getElementById("radarCountBadge");
    if (!tbody) return;

    try {
        const res = await fetch("/api/deca/setups");
        const data = await res.json();
        const setups = data.setups || [];
        if (badge) badge.innerText = setups.length;

        if (setups.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding:24px;">No active setups • Autonomous Scanner Scanning 20 Champions</td></tr>`;
        } else {
            tbody.innerHTML = setups.map(s => {
                const isLong = (s.side || '').toUpperCase() === 'LONG' || (s.side || '').toUpperCase() === 'BUY';
                const isAct = s.is_active || s.status === 'LIVE POSITION';
                const dist = s.distance_pct !== undefined ? Number(s.distance_pct) : Number(s.proximity_pct || 0.0);
                const pctClamped = Math.min(2.5, Math.max(0.0, dist));
                const progressWidth = Math.round(((2.5 - pctClamped) / 2.5) * 100);
                const barColor = dist <= 0.25 ? '#F59E0B' : (dist <= 0.6 ? 'var(--buy-green)' : 'var(--brand-teal)');

                if (isAct) {
                    const roe = Number(s.roe_pct || 0);
                    const roeSign = roe >= 0 ? '+' : '';
                    const roeColor = roe >= 0 ? 'var(--buy-green)' : 'var(--sell-red)';
                    return `
                        <tr style="cursor:pointer; background:rgba(0,245,155,0.04);" onclick="changePair('${s.symbol}')">
                            <td>
                                <span style="font-weight:800; color:var(--buy-green);"><i class="fa-solid fa-circle-dot" style="font-size:8px; margin-right:4px;"></i>${s.symbol}</span>
                            </td>
                            <td>
                                <span style="font-size:10px; padding:2px 6px; border-radius:3px; background:${isLong ? 'rgba(0,192,135,0.15)' : 'rgba(255,75,85,0.15)'}; color:${isLong ? 'var(--buy-green)' : 'var(--sell-red)'}; font-weight:800;">${isLong ? 'LONG' : 'SHORT'} ${s.timeframe || '4H'}</span>
                            </td>
                            <td><span style="color:var(--brand-teal); font-weight:700;">Section ${s.section_id}</span></td>
                            <td><b style="color:#fff;">$${Number(s.entry_price).toFixed(4)}</b></td>
                            <td><span style="color:var(--sell-red);">$${Number(s.sl_price).toFixed(4)}</span></td>
                            <td><span style="color:var(--buy-green);">$${Number(s.tp_price).toFixed(4)}</span></td>
                            <td><b style="color:${roeColor};">${roeSign}${roe.toFixed(2)}% ROE</b></td>
                            <td><span style="font-size:10px; background:rgba(0,245,155,0.2); color:var(--buy-green); border:1px solid rgba(0,245,155,0.4); padding:2px 6px; border-radius:4px; font-weight:800;">🔴 LIVE POSITION</span></td>
                        </tr>
                    `;
                }

                return `
                    <tr style="cursor:pointer;" onclick="changePair('${s.symbol}')">
                        <td>
                            <span style="font-weight:800; color:#fff;">${s.symbol}</span>
                        </td>
                        <td>
                            <span style="font-size:10px; padding:2px 6px; border-radius:3px; background:${isLong ? 'rgba(0,192,135,0.15)' : 'rgba(255,75,85,0.15)'}; color:${isLong ? 'var(--buy-green)' : 'var(--sell-red)'}; font-weight:800;">${isLong ? 'LONG' : 'SHORT'} ${s.timeframe || '4H'}</span>
                        </td>
                        <td><span style="color:var(--brand-teal); font-weight:700;">Section ${s.section_id}</span></td>
                        <td><b style="color:#fff;">$${Number(s.entry_price).toFixed(4)}</b></td>
                        <td><span style="color:var(--sell-red);">$${Number(s.sl_price).toFixed(4)}</span></td>
                        <td><span style="color:var(--buy-green);">$${Number(s.tp_price).toFixed(4)}</span></td>
                        <td>
                            <div style="display:flex; align-items:center; gap:6px;">
                                <div style="flex:1; height:4px; background:var(--bg-surface-elevated); border-radius:2px; overflow:hidden; min-width:35px;">
                                    <div style="width:${progressWidth}%; height:100%; background:${barColor};"></div>
                                </div>
                                <span style="font-size:11px; font-weight:800; color:${barColor};">${dist.toFixed(2)}% away</span>
                            </div>
                        </td>
                        <td><span style="font-size:10px; background:rgba(0,192,135,0.1); color:var(--buy-green); padding:2px 6px; border-radius:4px; font-weight:700;">${s.status}</span></td>
                    </tr>
                `;
            }).join("");
        }
    } catch (e) {
        console.error("Dock radar poll error:", e);
    }
}

async function pollSentries() {
    const btcEl = document.getElementById("sentryBtcStatus");
    if (!btcEl) return;
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        const btc = data.btc_macro_sentry || {};
        const chg = btc.change_pct != null ? btc.change_pct : 0.0;
        const veto = btc.long_veto ? "VETO (Dump Detected)" : "Safe (0 Veto)";
        btcEl.innerText = `BTC 4H Dump Guard: ${veto} (${chg >= 0 ? '+' : ''}${chg}%)`;
    } catch (e) {}
}

async function askDockAi() {
    const input = document.getElementById("dockAiInput");
    const respEl = document.getElementById("dockAiResponse");
    if (!input || !respEl) return;
    const prompt = input.value.trim();
    if (!prompt) return;

    respEl.innerHTML = `⏳ <i>Analyzing market structure with Gemini 2.5 Flash...</i>`;
    try {
        const res = await fetch("/api/ai/consult", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: prompt, symbol: currentSymbol })
        });
        const data = await res.json();
        const text = data.analysis || data.response || data.verdict || "No response received";
        respEl.innerHTML = `<div><b style="color:var(--brand-teal);">🤖 Gemini 2.5 Flash Analysis (${currentSymbol}):</b><p style="margin-top:6px; color:#fff;">${text.replace(/\n/g, '<br>')}</p></div>`;
    } catch (e) {
        respEl.innerHTML = `<span style="color:var(--sell-red);">Error consulting AI: ${e}</span>`;
    }
}

function quickAskDock(text) {
    const input = document.getElementById("dockAiInput");
    if (input) {
        input.value = text;
        askDockAi();
    }
}
