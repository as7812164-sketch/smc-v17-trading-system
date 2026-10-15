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

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
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
    pollOrderBook();
    pollPositions();
    pollSummary();

    setInterval(pollTicker, 2500);
    setInterval(pollOrderBook, 2500);
    setInterval(pollPositions, 3000);
    setInterval(pollSummary, 5000);
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

        if (pEl) {
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

        if (orderPriceInput && !orderPriceInput.dataset.manual) {
            orderPriceInput.value = t.last_price;
        }

        // Live chart tick update
        if (candleSeries) {
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
        if (capEl) capEl.innerText = `$${(s.total_balance / 10).toFixed(2)} USDT`;
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
            if (data.positions.length === 0) {
                tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:var(--text-muted); padding:30px;">No Open Positions • BB 2.0 Autonomous Scanner Standing By</td></tr>`;
            } else {
                tbody.innerHTML = data.positions.map(p => {
                    const isLong = p.side === 'LONG';
                    const sign = p.unrealized_pnl >= 0 ? '+' : '';
                    const pnlColor = p.unrealized_pnl >= 0 ? 'var(--buy-green)' : 'var(--sell-red)';
                    return `
                        <tr>
                            <td>
                                <span style="font-weight:800; color:#fff;">${p.symbol}</span>
                                <span style="font-size:10px; padding:2px 4px; border-radius:3px; background:${isLong ? 'rgba(0,192,135,0.15)' : 'rgba(255,75,85,0.15)'}; color:${isLong ? 'var(--buy-green)' : 'var(--sell-red)'}; font-weight:800; margin-left:4px;">${p.side} ${p.leverage}x</span>
                            </td>
                            <td>Section ${p.section_id}</td>
                            <td>$${p.position_size_usdt.toFixed(2)} ($${p.margin_usdt.toFixed(2)})</td>
                            <td>${p.entry_price.toFixed(4)}</td>
                            <td>${p.mark_price.toFixed(4)}</td>
                            <td><span style="color:${p.sl_price > p.entry_price ? 'var(--buy-green)' : 'var(--sell-red)'}">${p.trailing_sl_price > 0 ? p.trailing_sl_price.toFixed(4) : p.sl_price.toFixed(4)}</span></td>
                            <td><span style="color:var(--buy-green)">${p.tp_price.toFixed(4)}</span></td>
                            <td style="color:${pnlColor}; font-weight:800;">${sign}$${p.unrealized_pnl.toFixed(2)} (${sign}${p.pnl_pct.toFixed(2)}%)</td>
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
