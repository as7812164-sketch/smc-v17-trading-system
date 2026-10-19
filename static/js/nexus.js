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
let volumeSeries = null;
let ema20Series = null;
let ema50Series = null;
let ema200Series = null;
let currentChartPriceLines = [];
let currentSmcPriceLines = [];
let cachedActivePositions = [];
let cachedRadarSetups = [];
let activeChartStrategy = null;
let isHudManuallyHidden = false;

// Advanced Indicators & Replay Engine State
let currentFullCandles = [];
let indicatorsState = { ema: true, vol: true, smc: true };
let isReplayMode = false;
let replayCandles = [];
let replayIndex = 0;
let replayTimer = null;
let replaySpeedMs = 800;

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

// ----------------- ADVANCED TRADINGVIEW CHART ENGINE -----------------

function initChart() {
    const container = document.getElementById("tradingview_chart");
    if (!container || !window.LightweightCharts) return;

    if (chart) {
        try { chart.remove(); } catch(e) {}
    }

    const w = container.clientWidth || window.innerWidth || 360;
    const h = container.clientHeight || 340;

    chart = LightweightCharts.createChart(container, {
        width: w,
        height: h,
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

    // 1. Volume Histogram Series (Dedicated isolated scale, never distorts candlestick prices)
    volumeSeries = chart.addHistogramSeries({
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume_scale',
    });
    chart.priceScale('volume_scale').applyOptions({
        scaleMargins: {
            top: 0.80,
            bottom: 0,
        },
        visible: false,
    });

    // 2. Candlestick Series (Main Price)
    candleSeries = chart.addCandlestickSeries({
        upColor: '#00C087',
        downColor: '#FF4B55',
        borderVisible: false,
        wickUpColor: '#00C087',
        wickDownColor: '#FF4B55'
    });

    // Auto-scale right price scale dynamically for candlesticks with clean padding
    chart.priceScale('right').applyOptions({
        autoScale: true,
        scaleMargins: {
            top: 0.08,
            bottom: 0.22,
        },
    });

    // 3. EMA 20 (Yellow / Fast Trend)
    ema20Series = chart.addLineSeries({
        color: '#FFB800',
        lineWidth: 1.5,
        title: 'EMA 20',
        priceLineVisible: false,
    });

    // 4. EMA 50 (Cyan / Dynamic Base)
    ema50Series = chart.addLineSeries({
        color: '#00DFC0',
        lineWidth: 1.5,
        title: 'EMA 50',
        priceLineVisible: false,
    });

    // 5. EMA 200 (Purple / Institutional Macro)
    ema200Series = chart.addLineSeries({
        color: '#A78BFA',
        lineWidth: 2,
        title: 'EMA 200',
        priceLineVisible: false,
    });

    // Crosshair Live Tracker for OHLCV Tooltip Bar
    chart.subscribeCrosshairMove(onCrosshairMove);

    // Dynamic Chart Pan & Zoom sync for TradingView Measure Tool
    chart.timeScale().subscribeVisibleLogicalRangeChange(repositionMeasureOverlay);
    chart.timeScale().subscribeVisibleTimeRangeChange(repositionMeasureOverlay);

    // Initialize Measure Tool engine & event bindings
    initMeasureTool();

    window.addEventListener('resize', handleChartResize);
    document.addEventListener('fullscreenchange', handleChartResize);
    document.addEventListener('webkitfullscreenchange', handleChartResize);
}

function handleChartResize() {
    const container = document.getElementById("tradingview_chart");
    if (chart && container) {
        chart.applyOptions({ 
            width: container.clientWidth || window.innerWidth, 
            height: container.clientHeight || 340 
        });
        repositionMeasureOverlay();
    }
}

// ----------------- INDICATORS & CALCULATIONS -----------------

function calculateEMA(candles, period) {
    if (!candles || candles.length < period) return [];
    const k = 2 / (period + 1);
    let ema = 0;
    for (let i = 0; i < period; i++) {
        ema += candles[i].close;
    }
    ema /= period;

    const results = [{ time: candles[period - 1].time, value: Number(ema.toFixed(4)) }];
    for (let i = period; i < candles.length; i++) {
        ema = (candles[i].close * k) + (ema * (1 - k));
        results.push({ time: candles[i].time, value: Number(ema.toFixed(4)) });
    }
    return results;
}

function renderIndicators(candles) {
    if (!candles || candles.length === 0) return;

    // 1. Candlesticks
    if (candleSeries) candleSeries.setData(candles);

    // 2. Volume
    if (volumeSeries) {
        if (indicatorsState.vol) {
            const volData = candles.map(c => ({
                time: c.time,
                value: c.volume || 0,
                color: (c.close >= c.open) ? 'rgba(0, 192, 135, 0.45)' : 'rgba(255, 75, 85, 0.45)'
            }));
            volumeSeries.setData(volData);
        } else {
            volumeSeries.setData([]);
        }
    }

    // 3. EMA 20, 50, 200
    if (indicatorsState.ema) {
        const ema20 = calculateEMA(candles, 20);
        const ema50 = calculateEMA(candles, 50);
        const ema200 = calculateEMA(candles, Math.min(200, Math.max(20, Math.floor(candles.length * 0.7))));
        if (ema20Series) ema20Series.setData(ema20);
        if (ema50Series) ema50Series.setData(ema50);
        if (ema200Series) ema200Series.setData(ema200);

        // Update OHLC Bar EMA Labels
        const lastEma20 = ema20.length > 0 ? ema20[ema20.length - 1].value : '--';
        const lastEma50 = ema50.length > 0 ? ema50[ema50.length - 1].value : '--';
        const lastEma200 = ema200.length > 0 ? ema200[ema200.length - 1].value : '--';
        const e20El = document.getElementById("ohlcEma20");
        const e50El = document.getElementById("ohlcEma50");
        const e200El = document.getElementById("ohlcEma200");
        if (e20El) e20El.innerText = lastEma20;
        if (e50El) e50El.innerText = lastEma50;
        if (e200El) e200El.innerText = lastEma200;
    } else {
        if (ema20Series) ema20Series.setData([]);
        if (ema50Series) ema50Series.setData([]);
        if (ema200Series) ema200Series.setData([]);
    }

    // 4. Automated SMC Levels (PDH, PDL, 15m Extreme OB, 50% MT)
    updateSmcLevels(candles);
}

function updateSmcLevels(candles) {
    if (currentSmcPriceLines && currentSmcPriceLines.length > 0) {
        currentSmcPriceLines.forEach(l => {
            try { candleSeries.removePriceLine(l); } catch(e) {}
        });
        currentSmcPriceLines = [];
    }
    if (!indicatorsState.smc || !candleSeries || !candles || candles.length < 20) return;

    // A. PDH & PDL Detection
    const lookback = Math.min(candles.length - 2, 48);
    let pdh = -Infinity;
    let pdl = Infinity;
    for (let i = candles.length - lookback; i < candles.length - 2; i++) {
        if (candles[i].high > pdh) pdh = candles[i].high;
        if (candles[i].low < pdl) pdl = candles[i].low;
    }

    if (pdh > 0 && isFinite(pdh)) {
        const pdhLine = candleSeries.createPriceLine({
            price: pdh,
            color: '#FF4B55',
            lineWidth: 1,
            lineStyle: 2, // Dashed
            axisLabelVisible: true,
            title: `PDH (Liquidity Trap): $${pdh.toFixed(4)}`
        });
        currentSmcPriceLines.push(pdhLine);
    }

    if (pdl > 0 && isFinite(pdl)) {
        const pdlLine = candleSeries.createPriceLine({
            price: pdl,
            color: '#00F0FF',
            lineWidth: 1,
            lineStyle: 2, // Dashed
            axisLabelVisible: true,
            title: `PDL (Liquidity Sweep): $${pdl.toFixed(4)}`
        });
        currentSmcPriceLines.push(pdlLine);
    }

    // B. 15m Extreme Order Block & 50% Mean Threshold
    let bestDisp = 0;
    let obCandle = null;
    let obType = 'DEMAND';
    for (let i = candles.length - 22; i < candles.length - 3; i++) {
        if (i < 0 || i + 2 >= candles.length) continue;
        const move = Math.abs(candles[i+2].close - candles[i].open) / candles[i].open;
        if (move > bestDisp && move >= 0.012) {
            bestDisp = move;
            obCandle = candles[i];
            obType = candles[i+2].close > candles[i].open ? 'DEMAND' : 'SUPPLY';
        }
    }

    if (obCandle) {
        const obTop = Math.max(obCandle.open, obCandle.close, obCandle.high);
        const obBottom = Math.min(obCandle.open, obCandle.close, obCandle.low);
        const mt50 = obBottom + (obTop - obBottom) * 0.5;

        const mtLine = candleSeries.createPriceLine({
            price: mt50,
            color: '#FFB800',
            lineWidth: 2,
            lineStyle: 1, // Dotted
            axisLabelVisible: true,
            title: `50% MT Sniper Entry [${obType}]: $${mt50.toFixed(4)}`
        });
        currentSmcPriceLines.push(mtLine);
    }
}

// Indicator Toggle Handlers
function toggleEmaIndicator() {
    indicatorsState.ema = !indicatorsState.ema;
    const btn = document.getElementById("btnToggleEma");
    if (btn) btn.classList.toggle("active", indicatorsState.ema);
    renderIndicators(isReplayMode ? replayCandles.slice(0, replayIndex) : currentFullCandles);
}

function toggleVolumeIndicator() {
    indicatorsState.vol = !indicatorsState.vol;
    const btn = document.getElementById("btnToggleVol");
    if (btn) btn.classList.toggle("active", indicatorsState.vol);
    renderIndicators(isReplayMode ? replayCandles.slice(0, replayIndex) : currentFullCandles);
}

function toggleSmcLevels() {
    indicatorsState.smc = !indicatorsState.smc;
    const btn = document.getElementById("btnToggleSmc");
    if (btn) btn.classList.toggle("active", indicatorsState.smc);
    renderIndicators(isReplayMode ? replayCandles.slice(0, replayIndex) : currentFullCandles);
}

// ----------------- CROSSHAIR OHLCV TOOLTIP -----------------

function onCrosshairMove(param) {
    if (!param || !param.time || !candleSeries) {
        if (currentFullCandles.length > 0) {
            updateOhlcHeader(currentFullCandles[currentFullCandles.length - 1]);
        }
        return;
    }
    const candle = param.seriesData.get(candleSeries);
    if (candle) {
        updateOhlcHeader(candle);
    }
}

function updateOhlcHeader(bar) {
    if (!bar) return;
    const oEl = document.getElementById("ohlcO");
    const hEl = document.getElementById("ohlcH");
    const lEl = document.getElementById("ohlcL");
    const cEl = document.getElementById("ohlcC");
    const chgEl = document.getElementById("ohlcChg");
    const volEl = document.getElementById("ohlcVol");
    if (!cEl) return;

    if (oEl) oEl.innerText = Number(bar.open).toFixed(4);
    if (hEl) hEl.innerText = Number(bar.high).toFixed(4);
    if (lEl) lEl.innerText = Number(bar.low).toFixed(4);
    if (cEl) {
        cEl.innerText = Number(bar.close).toFixed(4);
        cEl.className = 'ohlc-val ' + (bar.close >= bar.open ? 'green' : 'red');
    }
    if (chgEl) {
        const chg = ((bar.close - bar.open) / bar.open) * 100;
        const sign = chg >= 0 ? '+' : '';
        chgEl.innerText = `${sign}${chg.toFixed(2)}%`;
        chgEl.className = 'ohlc-val ' + (chg >= 0 ? 'green' : 'red');
    }
    if (volEl) {
        const v = bar.volume || 0;
        volEl.innerText = v >= 1e6 ? (v/1e6).toFixed(2)+'M' : (v >= 1e3 ? (v/1e3).toFixed(1)+'K' : v.toFixed(0));
    }
}

// ----------------- FREE BAR REPLAY SIMULATOR -----------------

function toggleReplayMode() {
    if (isReplayMode) {
        exitReplayMode();
    } else {
        startReplayMode();
    }
}

function startReplayMode() {
    if (!currentFullCandles || currentFullCandles.length < 30) {
        alert("Candlestick data is loading, please wait a moment...");
        return;
    }
    isReplayMode = true;
    replayCandles = [...currentFullCandles];
    replayIndex = Math.max(15, replayCandles.length - 35); // Start 35 bars back
    
    const bar = document.getElementById("replayControllerBar");
    if (bar) bar.style.display = "flex";
    const btn = document.getElementById("btnToggleReplay");
    if (btn) btn.classList.add("btn-replay-active");

    const scrubber = document.getElementById("replayScrubber");
    if (scrubber) {
        scrubber.min = 15;
        scrubber.max = replayCandles.length;
        scrubber.value = replayIndex;
    }
    updateReplayDisplay();
}

function updateReplayDisplay() {
    const visible = replayCandles.slice(0, replayIndex);
    renderIndicators(visible);
    if (visible.length > 0) updateOhlcHeader(visible[visible.length - 1]);
    
    const cnt = document.getElementById("replayCounterText");
    if (cnt) cnt.innerText = `Bar ${replayIndex} / ${replayCandles.length}`;
    const scrubber = document.getElementById("replayScrubber");
    if (scrubber) scrubber.value = replayIndex;
}

function toggleReplayPlayPause() {
    const btn = document.getElementById("btnReplayPlayPause");
    if (replayTimer) {
        clearInterval(replayTimer);
        replayTimer = null;
        if (btn) {
            btn.innerHTML = '<i class="fa-solid fa-play"></i> Play';
            btn.classList.remove('active-play');
        }
    } else {
        if (replayIndex >= replayCandles.length) {
            replayIndex = Math.max(15, replayCandles.length - 35);
        }
        if (btn) {
            btn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
            btn.classList.add('active-play');
        }
        replayTimer = setInterval(stepReplayForward, replaySpeedMs);
    }
}

function stepReplayForward() {
    if (replayIndex < replayCandles.length) {
        const nextCandle = replayCandles[replayIndex++];
        if (candleSeries) candleSeries.update(nextCandle);
        if (volumeSeries && indicatorsState.vol) {
            volumeSeries.update({
                time: nextCandle.time,
                value: nextCandle.volume || 0,
                color: nextCandle.close >= nextCandle.open ? 'rgba(0, 192, 135, 0.45)' : 'rgba(255, 75, 85, 0.45)'
            });
        }
        updateOhlcHeader(nextCandle);
        const cnt = document.getElementById("replayCounterText");
        if (cnt) cnt.innerText = `Bar ${replayIndex} / ${replayCandles.length}`;
        const scrubber = document.getElementById("replayScrubber");
        if (scrubber) scrubber.value = replayIndex;
    } else {
        toggleReplayPlayPause();
    }
}

function stepReplayBackward() {
    if (replayIndex > 15) {
        replayIndex--;
        updateReplayDisplay();
    }
}

function resetReplayToStart() {
    replayIndex = Math.max(15, replayCandles.length - 35);
    updateReplayDisplay();
}

function onReplayScrubberChange(val) {
    replayIndex = parseInt(val, 10);
    updateReplayDisplay();
}

function setReplaySpeed(speed, btn) {
    document.querySelectorAll(".replay-speed-pill").forEach(b => b.classList.remove("active"));
    if (btn) btn.classList.add("active");
    if (speed === 1) replaySpeedMs = 800;
    else if (speed === 2) replaySpeedMs = 400;
    else if (speed === 5) replaySpeedMs = 150;

    if (replayTimer) {
        clearInterval(replayTimer);
        replayTimer = setInterval(stepReplayForward, replaySpeedMs);
    }
}

function exitReplayMode() {
    if (replayTimer) {
        clearInterval(replayTimer);
        replayTimer = null;
    }
    isReplayMode = false;
    const bar = document.getElementById("replayControllerBar");
    if (bar) bar.style.display = "none";
    const btn = document.getElementById("btnToggleReplay");
    if (btn) btn.classList.remove("btn-replay-active");
    const playBtn = document.getElementById("btnReplayPlayPause");
    if (playBtn) {
        playBtn.innerHTML = '<i class="fa-solid fa-play"></i> Play';
        playBtn.classList.remove('active-play');
    }
    if (candleSeries && currentFullCandles) {
        renderIndicators(currentFullCandles);
        if (currentFullCandles.length > 0) updateOhlcHeader(currentFullCandles[currentFullCandles.length - 1]);
    }
}

// ==========================================================================
// TRADINGVIEW PRICE RANGE / RULER / MEASURE TOOL ENGINE
// ==========================================================================

let isMeasureActive = false;
let isMeasuring = false;
let isDraggingHandle = null; // 1 or 2
let measurePoint1 = null; // { time, logical, price, x, y }
let measurePoint2 = null; // { time, logical, price, x, y }
let measurePriceLine = null;
let measureEventsInitialized = false;

function initMeasureTool() {
    const overlay = document.getElementById("measureToolOverlay");
    if (!overlay || measureEventsInitialized) return;
    measureEventsInitialized = true;

    // Pointer events on overlay for smooth desktop mouse & mobile touch drawing
    overlay.addEventListener("pointerdown", onMeasurePointerDown);
    overlay.addEventListener("pointermove", onMeasurePointerMove);
    overlay.addEventListener("pointerup", onMeasurePointerUp);
    overlay.addEventListener("pointercancel", onMeasurePointerUp);

    // Circular handles for dynamic re-adjusting
    const h1 = document.getElementById("measureHandle1");
    const h2 = document.getElementById("measureHandle2");

    if (h1) {
        h1.addEventListener("pointerdown", (e) => {
            e.stopPropagation();
            e.preventDefault();
            isDraggingHandle = 1;
            try { h1.setPointerCapture(e.pointerId); } catch(err) {}
        });
        h1.addEventListener("pointermove", onHandlePointerMove);
        h1.addEventListener("pointerup", onHandlePointerUp);
        h1.addEventListener("pointercancel", onHandlePointerUp);
    }

    if (h2) {
        h2.addEventListener("pointerdown", (e) => {
            e.stopPropagation();
            e.preventDefault();
            isDraggingHandle = 2;
            try { h2.setPointerCapture(e.pointerId); } catch(err) {}
        });
        h2.addEventListener("pointermove", onHandlePointerMove);
        h2.addEventListener("pointerup", onHandlePointerUp);
        h2.addEventListener("pointercancel", onHandlePointerUp);
    }

    // Global keyboard shortcuts (Escape / Delete to clear)
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" || e.key === "Delete" || e.key === "Backspace") {
            if (measurePoint1 || isMeasureActive) {
                clearMeasureTool();
            }
        }
    });
}

function toggleMeasureTool() {
    const btn = document.getElementById("btnToggleMeasure");
    const overlay = document.getElementById("measureToolOverlay");
    if (!overlay) return;

    if (isMeasureActive) {
        // If already in drawing mode without points, cancel
        if (isMeasuring || (!measurePoint1 && !measurePoint2)) {
            cancelMeasureMode();
            return;
        }
        // If already placed, clear existing and start new drawing
        clearMeasureTool();
        startMeasureMode();
    } else {
        if (measurePoint1 && measurePoint2) {
            clearMeasureTool();
        }
        startMeasureMode();
    }
}

function startMeasureMode() {
    isMeasureActive = true;
    isMeasuring = false;
    const btn = document.getElementById("btnToggleMeasure");
    if (btn) btn.classList.add("btn-measure-active");

    const overlay = document.getElementById("measureToolOverlay");
    if (overlay) {
        overlay.style.display = "block";
        overlay.classList.add("drawing-mode");
    }
}

function cancelMeasureMode() {
    isMeasureActive = false;
    isMeasuring = false;
    const btn = document.getElementById("btnToggleMeasure");
    if (btn) btn.classList.remove("btn-measure-active");

    const overlay = document.getElementById("measureToolOverlay");
    if (overlay) {
        overlay.classList.remove("drawing-mode");
        if (!measurePoint1 || !measurePoint2) {
            overlay.style.display = "none";
        }
    }
}

function clearMeasureTool(e) {
    if (e) {
        try { e.preventDefault(); e.stopPropagation(); } catch(err) {}
    }
    isMeasureActive = false;
    isMeasuring = false;
    isDraggingHandle = null;
    measurePoint1 = null;
    measurePoint2 = null;

    if (measurePriceLine && candleSeries) {
        try { candleSeries.removePriceLine(measurePriceLine); } catch(err) {}
        measurePriceLine = null;
    }

    const btn = document.getElementById("btnToggleMeasure");
    if (btn) btn.classList.remove("btn-measure-active");

    const overlay = document.getElementById("measureToolOverlay");
    if (overlay) {
        overlay.classList.remove("drawing-mode");
        overlay.style.display = "none";
    }

    const badge = document.getElementById("measureBadge");
    if (badge) badge.style.display = "none";

    const actionBar = document.getElementById("measureActionBar");
    if (actionBar) actionBar.style.display = "none";

    const box = document.getElementById("measureBox");
    if (box) { box.setAttribute("width", "0"); box.setAttribute("height", "0"); }
    const topL = document.getElementById("measureLineTop");
    if (topL) { topL.setAttribute("x1", "0"); topL.setAttribute("x2", "0"); }
    const btmL = document.getElementById("measureLineBottom");
    if (btmL) { btmL.setAttribute("x1", "0"); btmL.setAttribute("x2", "0"); }
    const ctrL = document.getElementById("measureLineCenter");
    if (ctrL) { ctrL.setAttribute("x1", "0"); ctrL.setAttribute("x2", "0"); }
    const h1 = document.getElementById("measureHandle1");
    if (h1) { h1.setAttribute("cx", "-999"); h1.setAttribute("cy", "-999"); }
    const h2 = document.getElementById("measureHandle2");
    if (h2) { h2.setAttribute("cx", "-999"); h2.setAttribute("cy", "-999"); }
}

function getMeasureCoordsFromEvent(e) {
    const container = document.getElementById("tradingview_chart");
    if (!container || !chart || !candleSeries) return null;
    const rect = container.getBoundingClientRect();
    const x = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
    const y = Math.max(0, Math.min(rect.height, e.clientY - rect.top));

    let time = null;
    let logical = null;
    try { time = chart.timeScale().coordinateToTime(x); } catch(err) {}
    try { logical = chart.timeScale().coordinateToLogical(x); } catch(err) {}
    let price = null;
    try { price = candleSeries.coordinateToPrice(y); } catch(err) {}

    if (price === null && currentFullCandles && currentFullCandles.length > 0) {
        price = currentFullCandles[currentFullCandles.length - 1].close;
    }

    if (!time && currentFullCandles && currentFullCandles.length > 0) {
        if (logical !== null) {
            const idx = Math.max(0, Math.min(currentFullCandles.length - 1, Math.round(logical)));
            time = currentFullCandles[idx].time;
        } else {
            time = currentFullCandles[currentFullCandles.length - 1].time;
        }
    }

    return { x, y, time, logical, price };
}

function onMeasurePointerDown(e) {
    if (!isMeasureActive) return;
    e.preventDefault();
    e.stopPropagation();

    const pt = getMeasureCoordsFromEvent(e);
    if (!pt || pt.price === null) return;

    if (!isMeasuring) {
        isMeasuring = true;
        measurePoint1 = pt;
        measurePoint2 = pt;
        renderMeasureGraphics(measurePoint1, measurePoint2);

        const overlay = document.getElementById("measureToolOverlay");
        if (overlay && overlay.setPointerCapture && e.pointerId !== undefined) {
            try { overlay.setPointerCapture(e.pointerId); } catch(err) {}
        }
    }
}

function onMeasurePointerMove(e) {
    if (!isMeasuring) return;
    e.preventDefault();
    e.stopPropagation();

    const pt = getMeasureCoordsFromEvent(e);
    if (!pt || pt.price === null) return;

    measurePoint2 = pt;
    renderMeasureGraphics(measurePoint1, measurePoint2);
}

function onMeasurePointerUp(e) {
    if (!isMeasuring) return;
    e.preventDefault();
    e.stopPropagation();

    isMeasuring = false;
    isMeasureActive = false;

    const pt = getMeasureCoordsFromEvent(e);
    if (pt && pt.price !== null) {
        measurePoint2 = pt;
    }

    // If drag was very small (< 10px), synthesize a clear visual range so user sees the tool
    if (measurePoint1 && measurePoint2 && Math.hypot(measurePoint2.x - measurePoint1.x, measurePoint2.y - measurePoint1.y) < 10) {
        const fallbackCandleCount = Math.min(25, Math.floor(currentFullCandles.length * 0.15));
        const p1Price = measurePoint1.price;
        const targetPrice = p1Price * 0.965; // ~3.5% move
        const targetY = candleSeries ? candleSeries.priceToCoordinate(targetPrice) : (measurePoint1.y + 60);
        measurePoint2 = {
            x: measurePoint1.x + 80,
            y: targetY || (measurePoint1.y + 60),
            price: targetPrice,
            time: measurePoint1.time,
            logical: (measurePoint1.logical || 0) + fallbackCandleCount
        };
    }

    // Finalize drawing mode
    const overlay = document.getElementById("measureToolOverlay");
    if (overlay) {
        overlay.classList.remove("drawing-mode");
    }
    const btn = document.getElementById("btnToggleMeasure");
    if (btn) btn.classList.remove("btn-measure-active");

    renderMeasureGraphics(measurePoint1, measurePoint2);
}

function onHandlePointerMove(e) {
    if (!isDraggingHandle || !measurePoint1 || !measurePoint2) return;
    e.preventDefault();
    e.stopPropagation();

    const pt = getMeasureCoordsFromEvent(e);
    if (!pt || pt.price === null) return;

    if (isDraggingHandle === 1) {
        measurePoint1 = pt;
    } else if (isDraggingHandle === 2) {
        measurePoint2 = pt;
    }
    renderMeasureGraphics(measurePoint1, measurePoint2);
}

function onHandlePointerUp(e) {
    if (!isDraggingHandle) return;
    e.preventDefault();
    e.stopPropagation();
    isDraggingHandle = null;
    renderMeasureGraphics(measurePoint1, measurePoint2);
}

function renderMeasureGraphics(p1, p2) {
    if (!p1 || !p2 || !chart || !candleSeries) return;

    // Convert prices to current pixel Y coordinates
    const y1 = candleSeries.priceToCoordinate(p1.price) ?? p1.y;
    const y2 = candleSeries.priceToCoordinate(p2.price) ?? p2.y;

    // Convert times/logicals to current pixel X coordinates
    let x1 = null;
    if (p1.time) {
        try { x1 = chart.timeScale().timeToCoordinate(p1.time); } catch(e) {}
    }
    if ((x1 === null || x1 === undefined) && p1.logical !== null && p1.logical !== undefined) {
        try { x1 = chart.timeScale().logicalToCoordinate(p1.logical); } catch(e) {}
    }
    if (x1 === null || x1 === undefined) x1 = p1.x;

    let x2 = null;
    if (p2.time) {
        try { x2 = chart.timeScale().timeToCoordinate(p2.time); } catch(e) {}
    }
    if ((x2 === null || x2 === undefined) && p2.logical !== null && p2.logical !== undefined) {
        try { x2 = chart.timeScale().logicalToCoordinate(p2.logical); } catch(e) {}
    }
    if (x2 === null || x2 === undefined) x2 = p2.x;

    const left = Math.min(x1, x2);
    const right = Math.max(x1, x2);
    const width = Math.max(2, right - left);

    const top = Math.min(y1, y2);
    const bottom = Math.max(y1, y2);
    const height = Math.max(2, bottom - top);

    // 1. Shaded Box
    const box = document.getElementById("measureBox");
    if (box) {
        box.setAttribute("x", left);
        box.setAttribute("y", top);
        box.setAttribute("width", width);
        box.setAttribute("height", height);
    }

    // 2. Top & Bottom Boundary Lines
    const topL = document.getElementById("measureLineTop");
    if (topL) {
        topL.setAttribute("x1", left);
        topL.setAttribute("y1", top);
        topL.setAttribute("x2", right);
        topL.setAttribute("y2", top);
    }
    const btmL = document.getElementById("measureLineBottom");
    if (btmL) {
        btmL.setAttribute("x1", left);
        btmL.setAttribute("y1", bottom);
        btmL.setAttribute("x2", right);
        btmL.setAttribute("y2", bottom);
    }

    // 3. Central Vertical Arrow Line
    const ctrL = document.getElementById("measureLineCenter");
    const midX = (left + right) / 2;
    if (ctrL) {
        ctrL.setAttribute("x1", midX);
        ctrL.setAttribute("y1", y1);
        ctrL.setAttribute("x2", midX);
        ctrL.setAttribute("y2", y2);
        if (y2 >= y1) {
            ctrL.setAttribute("marker-end", "url(#measureArrowDown)");
        } else {
            ctrL.setAttribute("marker-end", "url(#measureArrowUp)");
        }
    }

    // 4. Circular Handles
    const h1 = document.getElementById("measureHandle1");
    if (h1) {
        h1.setAttribute("cx", x1);
        h1.setAttribute("cy", y1);
    }
    const h2 = document.getElementById("measureHandle2");
    if (h2) {
        h2.setAttribute("cx", x2);
        h2.setAttribute("cy", y2);
    }

    // 5. Calculate Values: Δ Price, Δ %, Ticks
    const pStart = p1.price;
    const pEnd = p2.price;
    const diff = pEnd - pStart;
    const pct = pStart > 0 ? (diff / pStart) * 100 : 0;
    const sign = diff >= 0 ? "+" : "";

    let precision = 4;
    if (pStart > 1000) precision = 2;
    else if (pStart < 0.01) precision = 6;
    else if (pStart < 1) precision = 4;

    const diffText = `${sign}${diff.toFixed(precision)}`;
    const pctText = `(${sign}${pct.toFixed(2)}%)`;
    const ticksVal = Math.round(diff * Math.pow(10, Math.min(precision, 4)));

    // 6. Floating Badge Pill (TradingView exact format: "-0.228 (-4.65%) -228")
    const badge = document.getElementById("measureBadge");
    const badgeText = document.getElementById("measureBadgeText");
    if (badge && badgeText) {
        badgeText.innerText = `${diffText} ${pctText} ${ticksVal >= 0 ? '+' : ''}${ticksVal}`;
        badge.style.display = "block";

        const container = document.getElementById("tradingview_chart");
        const chartH = container ? container.clientHeight : 400;
        let badgeY = bottom + 12;
        if (badgeY + 28 > chartH) {
            badgeY = top - 32;
        }
        badge.style.left = `${Math.max(65, Math.min((container?.clientWidth || 360) - 75, midX))}px`;
        badge.style.top = `${badgeY}px`;
    }

    // 7. Floating Action Bar (Delete 🗑️ and Close)
    const actionBar = document.getElementById("measureActionBar");
    if (actionBar && !isMeasuring) {
        actionBar.style.display = "flex";
        let barY = top - 12;
        if (barY < 12) barY = bottom + 38;
        const container = document.getElementById("tradingview_chart");
        actionBar.style.left = `${Math.max(60, Math.min((container?.clientWidth || 360) - 60, midX))}px`;
        actionBar.style.top = `${barY}px`;
    }

    // 8. Right Price Scale Highlight Line (TradingView blue scale badge)
    if (candleSeries && !isMeasuring) {
        if (!measurePriceLine) {
            measurePriceLine = candleSeries.createPriceLine({
                price: pEnd,
                color: '#2962FF',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Solid,
                axisLabelVisible: true,
                title: 'Range'
            });
        } else {
            measurePriceLine.applyOptions({
                price: pEnd
            });
        }
    }
}

function repositionMeasureOverlay() {
    if (measurePoint1 && measurePoint2) {
        renderMeasureGraphics(measurePoint1, measurePoint2);
    }
}

// ----------------- FULLSCREEN & AUTO-LANDSCAPE CHART VIEW -----------------

let isChartLandscapeForced = false;

async function toggleChartFullscreen() {
    const elem = document.getElementById("chartSection");
    if (!elem) return;
    const isFull = document.fullscreenElement || document.webkitFullscreenElement;

    if (!isFull) {
        try {
            if (elem.requestFullscreen) {
                await elem.requestFullscreen();
            } else if (elem.webkitRequestFullscreen) {
                await elem.webkitRequestFullscreen();
            }
        } catch(e) {}

        // Auto-lock to LANDSCAPE mode!
        try {
            if (screen.orientation && screen.orientation.lock) {
                await screen.orientation.lock('landscape');
            }
        } catch(e) {
            // CSS Fallback rotation on mobile portrait
            if (window.innerWidth < window.innerHeight) {
                elem.classList.add('chart-forced-landscape');
                isChartLandscapeForced = true;
            }
        }
    } else {
        try {
            if (document.exitFullscreen) {
                await document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                await document.webkitExitFullscreen();
            }
        } catch(e) {}

        try {
            if (screen.orientation && screen.orientation.unlock) {
                screen.orientation.unlock();
            }
        } catch(e) {}

        elem.classList.remove('chart-forced-landscape');
        isChartLandscapeForced = false;
    }
    setTimeout(handleChartResize, 200);
}

function toggleChartOrientation() {
    const elem = document.getElementById("chartSection");
    if (!elem) return;
    isChartLandscapeForced = !isChartLandscapeForced;
    elem.classList.toggle('chart-forced-landscape', isChartLandscapeForced);
    setTimeout(handleChartResize, 150);
}

// ----------------- LOAD CANDLESTICKS (1-YEAR HISTORY SUPPORT) -----------------

async function loadKlines() {
    if (!candleSeries) return;
    try {
        // Multi-year deep history limit (up to 1,000 candles for 1d, 1w, 1M, and 300 for 15m/1h)
        let limit = 300;
        if (currentInterval === "1d" || currentInterval === "1w" || currentInterval === "1month") {
            limit = 1000;
        } else if (currentInterval === "4h" || currentInterval === "1h") {
            limit = 600;
        }

        const res = await fetch(`/api/klines/${currentSymbol}?interval=${currentInterval}&limit=${limit}`);
        const data = await res.json();
        if (data.candles && data.candles.length > 0) {
            currentFullCandles = data.candles;
            if (!isReplayMode) {
                renderIndicators(currentFullCandles);
                if (chart) chart.timeScale().fitContent();
                updateOhlcHeader(currentFullCandles[currentFullCandles.length - 1]);
            }

            // Auto-detect and render strategy levels for this pair
            const target = cachedActivePositions.find(p => p.symbol === currentSymbol) || cachedRadarSetups.find(s => s.symbol === currentSymbol);
            if (target) {
                drawStrategyOnChart(target, false);
            } else {
                clearChartStrategyLines();
                const hud = document.getElementById("chartStrategyHUD");
                if (hud) hud.style.display = "none";
                const toggleBtn = document.getElementById("chartStrategyToggleBtn");
                if (toggleBtn) toggleBtn.style.display = "none";
            }
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

// ----------------- STRATEGY CHART VISUALIZER (TV STYLE) -----------------

function clearChartStrategyLines() {
    if (candleSeries && currentChartPriceLines && currentChartPriceLines.length > 0) {
        currentChartPriceLines.forEach(line => {
            try {
                candleSeries.removePriceLine(line);
            } catch (err) {}
        });
        currentChartPriceLines = [];
    }
}

function drawStrategyOnChart(item, fitChart = false) {
    if (!item || !candleSeries) return;
    activeChartStrategy = item;

    // Clear previous lines
    clearChartStrategyLines();

    const isLong = (item.side_raw || item.side || '').toUpperCase() === 'LONG' || (item.side_raw || item.side || '').toUpperCase() === 'BUY';
    const sideStr = isLong ? 'LONG' : 'SHORT';
    const lev = (item.leverage || '5x').toString().replace('x', '') + 'x';
    const secId = item.section_id || item.account_id || 1;

    const entryP = Number(item.entry_price || 0);
    const markP = Number(item.mark_price || item.current_price || item.last_price || (document.getElementById("displayPrice")?.innerText.replace('$', '').replace(/,/g, '')) || entryP);
    const slP = Number(item.trailing_sl_price > 0 ? item.trailing_sl_price : (item.sl_price || 0));
    const tpP = Number(item.tp_price || 0);
    const isTrailing = Boolean(item.trailing_sl_price && item.trailing_sl_price > 0);
    const roe = item.roi_pct !== undefined ? Number(item.roi_pct) : Number(item.roe_pct || item.pnl_pct || 0);
    const uPnl = item.unrealized_pnl !== undefined ? Number(item.unrealized_pnl) : Number(item.unrealized_pnl_usdt || 0);
    const sign = uPnl >= 0 ? '+' : '';
    const pnlColor = uPnl >= 0 ? 'var(--buy-green)' : 'var(--sell-red)';

    // 1. Entry Price Line (Cyan / Teal)
    if (entryP > 0) {
        const eLine = candleSeries.createPriceLine({
            price: entryP,
            color: '#00DFC0',
            lineWidth: 2,
            lineStyle: 0, // Solid
            axisLabelVisible: true,
            title: `ENTRY: $${entryP.toFixed(4)} [${sideStr} ${lev}]`
        });
        currentChartPriceLines.push(eLine);
    }

    // 2. Stop Loss Line (Red)
    if (slP > 0) {
        const slLine = candleSeries.createPriceLine({
            price: slP,
            color: '#FF4B55',
            lineWidth: 2,
            lineStyle: 0, // Solid
            axisLabelVisible: true,
            title: `${isTrailing ? '🛡️ TRAILING SL' : '⛔ STOP LOSS'}: $${slP.toFixed(4)}`
        });
        currentChartPriceLines.push(slLine);
    }

    // 3. Take Profit Line (Green)
    if (tpP > 0) {
        const tpLine = candleSeries.createPriceLine({
            price: tpP,
            color: '#00C087',
            lineWidth: 2,
            lineStyle: 0, // Solid
            axisLabelVisible: true,
            title: `🎯 TARGET TP: $${tpP.toFixed(4)} (+3.0R)`
        });
        currentChartPriceLines.push(tpLine);
    }

    // 4. Mean Threshold Line (if setup / OB)
    const mt = Number(item.mean_threshold || item.mt || 0);
    if (mt > 0) {
        const mtLine = candleSeries.createPriceLine({
            price: mt,
            color: '#F59E0B',
            lineWidth: 1,
            lineStyle: 2, // Dashed
            axisLabelVisible: true,
            title: `⚡ 50% MT: $${mt.toFixed(4)}`
        });
        currentChartPriceLines.push(mtLine);
    }

    // Update HUD DOM Elements
    const hud = document.getElementById("chartStrategyHUD");
    const toggleBtn = document.getElementById("chartStrategyToggleBtn");
    if (toggleBtn) toggleBtn.style.display = "inline-flex";

    const sideBadge = document.getElementById("hudSideBadge");
    if (sideBadge) {
        sideBadge.innerText = `${sideStr} ${lev}`;
        sideBadge.className = `hud-pill ${isLong ? 'pill-long' : 'pill-short'}`;
    }

    const secBadge = document.getElementById("hudSectionBadge");
    if (secBadge) secBadge.innerText = `Section #${secId}`;

    const entryEl = document.getElementById("hudEntryPrice");
    if (entryEl) entryEl.innerText = `$${entryP.toFixed(4)}`;

    const markEl = document.getElementById("hudMarkPrice");
    if (markEl) markEl.innerText = `$${markP.toFixed(4)}`;

    const slEl = document.getElementById("hudSlPrice");
    if (slEl) {
        slEl.innerText = `$${slP.toFixed(4)}`;
        slEl.className = `hud-val ${slP > entryP ? 'green' : 'red'}`;
    }

    const tpEl = document.getElementById("hudTpPrice");
    if (tpEl) tpEl.innerText = `$${tpP.toFixed(4)}`;

    const pnlEl = document.getElementById("hudPnlValue");
    if (pnlEl) {
        pnlEl.innerText = `${sign}$${uPnl.toFixed(2)} (${sign}${roe.toFixed(2)}% ROI)`;
        pnlEl.style.color = pnlColor;
    }

    const stageEl = document.getElementById("hudTrailingStageText");
    if (stageEl) {
        if (isTrailing) {
            stageEl.innerHTML = `🛡️ <b>Trailing Active</b>: SL Protected at $${slP.toFixed(4)} (Continuous ROI Lock)`;
        } else {
            stageEl.innerHTML = `⚡ <b>Armored Setup</b>: Trailing Trigger at +4.80% ROI ➔ Locks +1.00% Profit`;
        }
    }

    if (hud && !isHudManuallyHidden) {
        hud.style.display = "block";
    }

    if (fitChart && chart) {
        try {
            chart.timeScale().fitContent();
        } catch(e) {}
    }
}

function selectPositionOnChart(symbol) {
    if (!symbol) return;
    const sym = symbol.toUpperCase();
    if (currentSymbol !== sym) {
        changePair(sym);
    }
    
    isHudManuallyHidden = false;

    // Find in active positions first, then radar setups
    let target = cachedActivePositions.find(p => p.symbol === sym);
    if (!target) {
        target = cachedRadarSetups.find(s => s.symbol === sym);
    }

    if (target) {
        setTimeout(() => {
            drawStrategyOnChart(target, true);
        }, 300);
    }

    // Scroll to chart smoothly so trader sees the levels immediately
    const chartEl = document.querySelector(".chart-container");
    if (chartEl && window.innerWidth <= 960) {
        chartEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function toggleChartStrategyHUD(e) {
    if (e) e.stopPropagation();
    const hud = document.getElementById("chartStrategyHUD");
    if (!hud) return;
    if (hud.style.display === "none") {
        isHudManuallyHidden = false;
        hud.style.display = "block";
    } else {
        isHudManuallyHidden = true;
        hud.style.display = "none";
    }
}

function onChartAreaClick(e) {
    if (isMeasureActive || isMeasuring) return;
    // If user clicks on the chart container, reveal / refresh strategy lines
    const hud = document.getElementById("chartStrategyHUD");
    const target = cachedActivePositions.find(p => p.symbol === currentSymbol) || cachedRadarSetups.find(s => s.symbol === currentSymbol);
    if (target) {
        if (hud && hud.style.display === "none") {
            isHudManuallyHidden = false;
            hud.style.display = "block";
        }
        drawStrategyOnChart(target, false);
    }
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

        // Live chart tick update (safe monotonic update)
        if (candleSeries && t.last_price > 0) {
            try {
                candleSeries.update({
                    time: Math.floor(Date.now() / 1000),
                    open: t.last_price,
                    high: t.last_price,
                    low: t.last_price,
                    close: t.last_price
                });
            } catch (tickErr) {
                // Ignore any time-order exception from rapid updates
            }
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

        const drawerEq = document.getElementById("drawerTotalEquity");
        if (drawerEq && s.total_equity !== undefined) {
            drawerEq.innerText = `$${s.total_equity.toFixed(2)} USDT`;
        }
        const drawerMode = document.getElementById("drawerActiveMode");
        if (drawerMode && s.mode) {
            drawerMode.innerText = s.mode;
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
        cachedActivePositions = data.positions || [];

        // If current symbol has an active open position, keep chart strategy & HUD in sync
        const currentActivePos = cachedActivePositions.find(p => p.symbol === currentSymbol);
        if (currentActivePos) {
            drawStrategyOnChart(currentActivePos, false);
        }

        const tbody = document.getElementById("positionsTableBody");
        const countBadge = document.getElementById("posCountBadge");
        if (countBadge) countBadge.innerText = data.count;

        if (tbody) {
            if (!data.positions || data.positions.length === 0) {
                tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:var(--text-muted); padding:30px;">No Open Positions • BB 3.0 Autonomous Scanner Standing By</td></tr>`;
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
                        <tr class="clickable-row" onclick="selectPositionOnChart('${p.symbol}')" title="Click to view full strategy on chart!">
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
                                <button class="btn-close-pos" onclick="event.stopPropagation(); closePosition(${p.id})">Close</button>
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
        cachedRadarSetups = setups;
        if (badge) badge.innerText = setups.length;

        // If current pair is on radar (and no active position), refresh its strategy lines
        if (!cachedActivePositions.some(p => p.symbol === currentSymbol)) {
            const currentSetup = cachedRadarSetups.find(s => s.symbol === currentSymbol);
            if (currentSetup) {
                drawStrategyOnChart(currentSetup, false);
            }
        }

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
                        <tr class="clickable-row" style="cursor:pointer; background:rgba(0,245,155,0.04);" onclick="selectPositionOnChart('${s.symbol}')" title="Click to view position on chart!">
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
                    <tr class="clickable-row" style="cursor:pointer;" onclick="selectPositionOnChart('${s.symbol}')" title="Click to view setup on chart!">
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
