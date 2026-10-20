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

    // Pure Candlestick Series (No EMA lines, No Volume Series)
    candleSeries = chart.addCandlestickSeries({
        upColor: '#00C087',
        downColor: '#FF4B55',
        borderVisible: false,
        wickUpColor: '#00C087',
        wickDownColor: '#FF4B55'
    });

    volumeSeries = null;
    ema20Series = null;
    ema50Series = null;
    ema200Series = null;

    // Auto-scale right price scale dynamically with pure candlestick padding
    chart.priceScale('right').applyOptions({
        autoScale: true,
        scaleMargins: {
            top: 0.08,
            bottom: 0.08,
        },
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

    // 1. Pure Candlesticks
    if (candleSeries) candleSeries.setData(candles);

    // 2. Automated SMC Levels (PDH, PDL, 15m Extreme OB, 50% MT)
    updateSmcLevels(candles);

    // 3. Hermes 3.0 Strategy Markers & Live Open Position Markers
    renderNexusStrategyMarkers(candles);
}

function scanAllHermes30Setups(candles) {
    const setups = [];
    if (!candles || candles.length < 20) return setups;

    let minDisp = 0.012;
    if (currentTimeframe === '1h') minDisp = 0.020;
    else if (currentTimeframe === '4h' || currentTimeframe === '1d') minDisp = 0.035;

    const n = candles.length;
    for (let i = 15; i < n - 2; i++) {
        // BULLISH (LONG) SETUP CHECK
        const priorLows = candles.slice(Math.max(0, i - 12), i + 1).map(c => c.low);
        if (candles[i].low === Math.min(...priorLows)) {
            const subWindow = candles.slice(i, Math.min(i + 14, n));
            const subHighs = subWindow.map(c => c.high);
            const maxHigh = Math.max(...subHighs);
            const peakIdx = i + subHighs.indexOf(maxHigh);

            if (peakIdx > i + 2) {
                const originL = candles[i].low;
                const gain = (maxHigh - originL) / originL;

                if (gain >= minDisp) {
                    const idmLow = candles[peakIdx - 1].low;
                    let bestMid = -1;
                    let maxRange = 0;

                    for (let mid = i + 1; mid < peakIdx; mid++) {
                        const cMid = candles[mid];
                        const fib = (cMid.low - originL) / (maxHigh - originL);
                        if (fib >= 0.25 && fib <= 0.75) {
                            const r = cMid.high - cMid.low;
                            if (r > maxRange) {
                                maxRange = r;
                                bestMid = mid;
                            }
                        }
                    }

                    if (bestMid !== -1) {
                        const decC = candles[bestMid - 1] || candles[bestMid];
                        const decTop = Math.max(decC.open, decC.close);
                        const decBot = decC.low;
                        const mt = (decTop + decBot) / 2.0;

                        for (let t = peakIdx + 1; t < Math.min(peakIdx + 20, n); t++) {
                            const tapC = candles[t];
                            const isTapping = (tapC.low <= mt * 1.003 && tapC.close >= mt * 0.994);
                            const swept = candles.slice(peakIdx, t + 1).some(c => c.low <= idmLow);
                            const cRange = tapC.high - tapC.low;
                            const lowerWick = Math.min(tapC.open, tapC.close) - tapC.low;
                            const wickRatio = cRange > 0 ? (lowerWick / cRange) : 0;

                            if (isTapping && swept && wickRatio >= 0.15) {
                                setups.push({
                                    side: "BUY",
                                    type: "LONG",
                                    entryPrice: mt,
                                    tpPrice: mt * 1.028,
                                    hardSlPrice: mt * 0.972,
                                    candleIndex: t,
                                    candleTime: tapC.time
                                });
                                break;
                            }
                        }
                    }
                }
            }
        }

        // BEARISH (SHORT) SETUP CHECK
        const priorHighs = candles.slice(Math.max(0, i - 12), i + 1).map(c => c.high);
        if (candles[i].high === Math.max(...priorHighs)) {
            const subWindow = candles.slice(i, Math.min(i + 14, n));
            const subLows = subWindow.map(c => c.low);
            const minLow = Math.min(...subLows);
            const troughIdx = i + subLows.indexOf(minLow);

            if (troughIdx > i + 2) {
                const originH = candles[i].high;
                const drop = (originH - minLow) / originH;

                if (drop >= minDisp) {
                    const idmHigh = candles[troughIdx - 1].high;
                    let bestMid = -1;
                    let maxRange = 0;

                    for (let mid = i + 1; mid < troughIdx; mid++) {
                        const cMid = candles[mid];
                        const fib = (originH - cMid.high) / (originH - minLow);
                        if (fib >= 0.25 && fib <= 0.75) {
                            const r = cMid.high - cMid.low;
                            if (r > maxRange) {
                                maxRange = r;
                                bestMid = mid;
                            }
                        }
                    }

                    if (bestMid !== -1) {
                        const decC = candles[bestMid - 1] || candles[bestMid];
                        const decTop = decC.high;
                        const decBot = Math.min(decC.open, decC.close);
                        const mt = (decTop + decBot) / 2.0;

                        for (let t = troughIdx + 1; t < Math.min(troughIdx + 20, n); t++) {
                            const tapC = candles[t];
                            const isTapping = (tapC.high >= mt * 0.997 && tapC.close <= mt * 1.006);
                            const swept = candles.slice(troughIdx, t + 1).some(c => c.high >= idmHigh);
                            const cRange = tapC.high - tapC.low;
                            const upperWick = tapC.high - Math.max(tapC.open, tapC.close);
                            const wickRatio = cRange > 0 ? (upperWick / cRange) : 0;

                            if (isTapping && swept && wickRatio >= 0.15) {
                                setups.push({
                                    side: "SELL",
                                    type: "SHORT",
                                    entryPrice: mt,
                                    tpPrice: mt * 0.972,
                                    hardSlPrice: mt * 1.028,
                                    candleIndex: t,
                                    candleTime: tapC.time
                                });
                                break;
                            }
                        }
                    }
                }
            }
        }
    }
    return setups;
}

function renderNexusStrategyMarkers(candles) {
    if (!candleSeries || !candles || candles.length === 0) return;
    const markers = [];

    // 1. Live Active Position Marker (if coin is in open position)
    const symUpper = currentSymbol ? currentSymbol.toUpperCase() : '';
    const activePos = (cachedActivePositions || []).find(p => (p.symbol || '').toUpperCase() === symUpper);
    if (activePos) {
        let entryTimeSec = activePos.entry_time || 0;
        if (entryTimeSec > 1e11) entryTimeSec = Math.floor(entryTimeSec / 1000);
        let closestCandle = null;
        if (entryTimeSec > 0) {
            closestCandle = candles.find(c => c.time >= entryTimeSec);
        }
        if (!closestCandle) closestCandle = candles[candles.length - 1];

        const isLong = (activePos.side || '').toUpperCase() === 'BUY' || (activePos.side_raw || '').toUpperCase() === 'LONG';
        const ep = activePos.entry_price || 0;
        const roe = activePos.roe_str || (activePos.pnl_pct ? `${activePos.pnl_pct}%` : '+0.00%');

        markers.push({
            time: closestCandle.time,
            position: isLong ? 'belowBar' : 'aboveBar',
            color: isLong ? '#00DFC0' : '#FF4B55',
            shape: isLong ? 'arrowUp' : 'arrowDown',
            text: `${isLong ? '🟢 ACTIVE BUY' : '🔴 ACTIVE SELL'} @ $${ep.toFixed(ep < 1 ? 4 : 2)} (${roe})`,
            size: 2
        });
    }

    // 2. Hermes 3.0 Model 2A Strategy Setup Markers
    const setups = scanAllHermes30Setups(candles);
    const maxTime = (isReplayMode && replayIndex > 0 && replayCandles[replayIndex - 1]) ? replayCandles[replayIndex - 1].time : Infinity;
    for (const s of setups) {
        if (s.candleTime <= maxTime) {
            const isLong = s.side === 'BUY';
            const ep = s.entryPrice;
            markers.push({
                time: s.candleTime,
                position: isLong ? 'belowBar' : 'aboveBar',
                color: isLong ? '#00C087' : '#FF4B55',
                shape: isLong ? 'arrowUp' : 'arrowDown',
                text: `Hermes 3.0 ${s.type} @ $${ep.toFixed(ep < 1 ? 4 : 2)}`,
                size: 1.5
            });
        }
    }

    markers.sort((a, b) => a.time - b.time);
    try {
        candleSeries.setMarkers(markers);
    } catch(e) {}
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

// ----------------- FREE BAR REPLAY & HERMES 3.0 MODEL 2A BACKTEST ENGINE -----------------

let isHermesReplayStratActive = true;
let isReplayAutoTrade = false;
let replaySimTrade = null; // { active, side, entryPrice, slPrice, hardSlPrice, tpPrice, peakRoi, currentStep, lockedRoi, durationBars, filled }
let replayCurrentSetup = null;
let replaySimJournal = []; // [ { id, symbol, side, entryPrice, exitPrice, outcome, roePct, pnlUsdt, durationBars, exitTime, lockedRoi } ]
let replayPriceLines = { entry: null, tp: null, sl: null, trailing: null };
let bannerTimeout = null;

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
    replayIndex = Math.max(25, replayCandles.length - 45); // Start 45 bars back for rich backtesting
    
    const bar = document.getElementById("replayControllerBar");
    if (bar) bar.style.display = "flex";
    const btn = document.getElementById("btnToggleReplay");
    if (btn) btn.classList.add("btn-replay-active");

    const scrubber = document.getElementById("replayScrubber");
    if (scrubber) {
        scrubber.min = 25;
        scrubber.max = replayCandles.length;
        scrubber.value = replayIndex;
    }
    updateReplayDisplay();
}

function updateReplayDisplay() {
    const visible = replayCandles.slice(0, replayIndex);
    renderIndicators(visible);
    if (visible.length > 0) {
        const lastBar = visible[visible.length - 1];
        updateOhlcHeader(lastBar);
        
        // Strategy Setup Evaluation on visible bars
        if (isHermesReplayStratActive) {
            checkHermes30SetupOnReplay(visible);
        }
        
        // Active Trade Simulation Evaluation
        if (replaySimTrade && replaySimTrade.active) {
            evaluateActiveReplaySimTrade(lastBar);
        }
    }
    
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
            replayIndex = Math.max(25, replayCandles.length - 45);
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
        
        const visible = replayCandles.slice(0, replayIndex);
        
        // Hermes 3.0 Model 2A Check
        if (isHermesReplayStratActive) {
            checkHermes30SetupOnReplay(visible);
        }
        
        // Live Simulated Trade Evaluation
        if (replaySimTrade && replaySimTrade.active) {
            evaluateActiveReplaySimTrade(nextCandle);
        }
    } else {
        toggleReplayPlayPause();
    }
}

function stepReplayBackward() {
    if (replayIndex > 25) {
        replayIndex--;
        updateReplayDisplay();
    }
}

function resetReplayToStart() {
    replayIndex = Math.max(25, replayCandles.length - 45);
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

function toggleReplayHermesStrategy() {
    isHermesReplayStratActive = !isHermesReplayStratActive;
    const btn = document.getElementById("btnReplayHermesStrat");
    const txt = document.getElementById("replayStratText");
    if (btn) {
        if (isHermesReplayStratActive) {
            btn.classList.add("active-strat");
            if (txt) txt.innerText = "Hermes 2A: ON";
        } else {
            btn.classList.remove("active-strat");
            if (txt) txt.innerText = "Hermes 2A: OFF";
            dismissReplaySignal();
        }
    }
}

function toggleReplayAutoTrade() {
    isReplayAutoTrade = !isReplayAutoTrade;
    const btn = document.getElementById("btnReplayAutoTrade");
    const txt = document.getElementById("replayAutoText");
    if (btn) {
        if (isReplayAutoTrade) {
            btn.classList.add("active-auto");
            if (txt) txt.innerText = "Auto: ON";
        } else {
            btn.classList.remove("active-auto");
            if (txt) txt.innerText = "Auto: OFF";
        }
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
    dismissReplaySignal();
    clearReplayChartPriceLines();
    const activeHud = document.getElementById("replayActiveTradeHUD");
    if (activeHud) activeHud.style.display = "none";
    
    if (candleSeries && currentFullCandles) {
        renderIndicators(currentFullCandles);
        if (currentFullCandles.length > 0) updateOhlcHeader(currentFullCandles[currentFullCandles.length - 1]);
    }
}

// ----------------- HERMES 3.0 MODEL 2A DETECTION ENGINE -----------------

function checkHermes30SetupOnReplay(candles) {
    if (!candles || candles.length < 25) return;
    
    // Don't show new signal if trade is currently active
    if (replaySimTrade && replaySimTrade.active) {
        dismissReplaySignal();
        return;
    }
    
    const setup = detectHermes30Setup(candles);
    if (setup) {
        // If this is a fresh setup or hasn't been executed
        if (!replayCurrentSetup || replayCurrentSetup.candleIndex !== setup.candleIndex || replayCurrentSetup.side !== setup.side) {
            replayCurrentSetup = setup;
            showReplaySignalCard(setup);
            playInstitutionalChime("signal");
            
            // Auto execute if enabled
            if (isReplayAutoTrade) {
                executeCurrentReplaySignal();
            }
        }
    } else {
        // Only dismiss if the current setup is more than 3 bars old
        if (replayCurrentSetup && (candles.length - 1 - replayCurrentSetup.candleIndex > 4)) {
            dismissReplaySignal();
            replayCurrentSetup = null;
        }
    }
}

function detectHermes30Setup(candles) {
    const n = candles.length;
    const curr = candles[n - 1];
    
    let minDisp = 0.025; // 2.5% default
    if (currentInterval === '15m') minDisp = 0.015;
    else if (currentInterval === '1h') minDisp = 0.022;
    else if (currentInterval === '4h' || currentInterval === '1d') minDisp = 0.038;
    
    const lookback = Math.min(35, n - 4);
    const startIdx = Math.max(0, n - lookback);
    
    // 1. BULLISH (BUY / LONG) MODEL 2A CHECK
    let originLow = Infinity;
    let originIdx = -1;
    for (let i = startIdx; i < n - 6; i++) {
        if (candles[i].low < originLow) {
            originLow = candles[i].low;
            originIdx = i;
        }
    }
    
    if (originIdx !== -1 && originLow > 0) {
        let peakHigh = -Infinity;
        let peakIdx = -1;
        for (let i = originIdx + 2; i < n - 2; i++) {
            if (candles[i].high > peakHigh) {
                peakHigh = candles[i].high;
                peakIdx = i;
            }
        }
        
        if (peakIdx > originIdx + 2) {
            const gain = (peakHigh - originLow) / originLow;
            if (gain >= minDisp) {
                const idmLow = candles[peakIdx - 1].low;
                let bestMid = -1;
                let maxR = 0;
                for (let mid = originIdx + 1; mid < peakIdx; mid++) {
                    const cMid = candles[mid];
                    const fib = (cMid.low - originLow) / (peakHigh - originLow);
                    if (fib >= 0.28 && fib <= 0.72) {
                        const r = cMid.high - cMid.low;
                        const hasFvg = (mid + 1 < n && mid - 1 >= 0) ? (candles[mid + 1].low > candles[mid - 1].high) : true;
                        if (hasFvg && r > maxR) {
                            maxR = r;
                            bestMid = mid;
                        }
                    }
                }
                
                if (bestMid !== -1) {
                    const decC = candles[bestMid - 1] || candles[bestMid];
                    const decTop = Math.max(decC.open, decC.close);
                    const decBot = decC.low;
                    const mt = (decTop + decBot) / 2.0;
                    
                    const sweptIdm = candles.slice(peakIdx, n).some(c => c.low < idmLow);
                    const isTapping = (curr.low <= mt * 1.0025 && curr.close >= mt * 0.995);
                    const cRange = curr.high - curr.low;
                    const lowerWick = Math.min(curr.open, curr.close) - curr.low;
                    const wickRatio = cRange > 0 ? (lowerWick / cRange) : 0;
                    
                    if (sweptIdm && isTapping && wickRatio >= 0.18) {
                        const tpPrice = mt * (1.0 + 0.028); // +2.80% price move = +14% ROE @ 5x
                        const softSlPrice = mt * (1.0 - 0.015);
                        const hardSlPrice = mt * (1.0 - 0.028);
                        return {
                            symbol: currentSymbol,
                            side: "BUY",
                            type: "LONG",
                            entryPrice: mt,
                            obHigh: decTop,
                            obLow: decBot,
                            tpPrice: tpPrice,
                            softSlPrice: softSlPrice,
                            hardSlPrice: hardSlPrice,
                            displacementPct: (gain * 100).toFixed(2),
                            wickRatioPct: (wickRatio * 100).toFixed(1),
                            candleIndex: n - 1,
                            candleTime: curr.time
                        };
                    }
                }
            }
        }
    }
    
    // 2. BEARISH (SELL / SHORT) MODEL 2A CHECK
    let originHigh = -Infinity;
    let originHighIdx = -1;
    for (let i = startIdx; i < n - 6; i++) {
        if (candles[i].high > originHigh) {
            originHigh = candles[i].high;
            originHighIdx = i;
        }
    }
    
    if (originHighIdx !== -1 && originHigh > 0) {
        let troughLow = Infinity;
        let troughIdx = -1;
        for (let i = originHighIdx + 2; i < n - 2; i++) {
            if (candles[i].low < troughLow) {
                troughLow = candles[i].low;
                troughIdx = i;
            }
        }
        
        if (troughIdx > originHighIdx + 2) {
            const drop = (originHigh - troughLow) / originHigh;
            if (drop >= minDisp) {
                const idmHigh = candles[troughIdx - 1].high;
                let bestMid = -1;
                let maxR = 0;
                for (let mid = originHighIdx + 1; mid < troughIdx; mid++) {
                    const cMid = candles[mid];
                    const fib = (originHigh - cMid.high) / (originHigh - troughLow);
                    if (fib >= 0.28 && fib <= 0.72) {
                        const r = cMid.high - cMid.low;
                        const hasBearFvg = (mid + 1 < n && mid - 1 >= 0) ? (candles[mid + 1].high < candles[mid - 1].low) : true;
                        if (hasBearFvg && r > maxR) {
                            maxR = r;
                            bestMid = mid;
                        }
                    }
                }
                
                if (bestMid !== -1) {
                    const decC = candles[bestMid - 1] || candles[bestMid];
                    const decTop = decC.high;
                    const decBot = Math.min(decC.open, decC.close);
                    const mt = (decTop + decBot) / 2.0;
                    
                    const sweptIdm = candles.slice(troughIdx, n).some(c => c.high > idmHigh);
                    const isTapping = (curr.high >= mt * 0.9975 && curr.close <= mt * 1.005);
                    const cRange = curr.high - curr.low;
                    const upperWick = curr.high - Math.max(curr.open, curr.close);
                    const wickRatio = cRange > 0 ? (upperWick / cRange) : 0;
                    
                    if (sweptIdm && isTapping && wickRatio >= 0.18) {
                        const tpPrice = mt * (1.0 - 0.028); // -2.80% move = +14.0% ROE @ 5x
                        const softSlPrice = mt * (1.0 + 0.015);
                        const hardSlPrice = mt * (1.0 + 0.028);
                        return {
                            symbol: currentSymbol,
                            side: "SELL",
                            type: "SHORT",
                            entryPrice: mt,
                            obHigh: decTop,
                            obLow: decBot,
                            tpPrice: tpPrice,
                            softSlPrice: softSlPrice,
                            hardSlPrice: hardSlPrice,
                            displacementPct: (drop * 100).toFixed(2),
                            wickRatioPct: (wickRatio * 100).toFixed(1),
                            candleIndex: n - 1,
                            candleTime: curr.time
                        };
                    }
                }
            }
        }
    }
    
    return null;
}

function showReplaySignalCard(setup) {
    const card = document.getElementById("replaySignalHUD");
    if (!card) return;
    
    const isLong = setup.side === "BUY";
    const badge = document.getElementById("rscSignalBadge");
    if (badge) {
        badge.className = `rsc-badge ${isLong ? 'rsc-badge-long' : 'rsc-badge-short'}`;
        badge.innerHTML = isLong 
            ? '<i class="fa-solid fa-arrow-trend-up"></i> HERMES 3.0 MODEL 2A • LONG BUY' 
            : '<i class="fa-solid fa-arrow-trend-down"></i> HERMES 3.0 MODEL 2A • SHORT SELL';
    }
    
    const ep = document.getElementById("rscEntryPrice");
    if (ep) ep.innerText = `$${setup.entryPrice.toFixed(4)}`;
    const tp = document.getElementById("rscTpPrice");
    if (tp) tp.innerText = `$${setup.tpPrice.toFixed(4)} (+14% ROE)`;
    const sl = document.getElementById("rscSlPrice");
    if (sl) sl.innerText = `$${setup.hardSlPrice.toFixed(4)} (-14% ROE)`;
    const dw = document.getElementById("rscDispWick");
    if (dw) dw.innerText = `+${setup.displacementPct}% / ${setup.wickRatioPct}% Wick`;
    
    const btn = document.getElementById("btnExecuteReplayTrade");
    if (btn) {
        btn.innerHTML = `<i class="fa-solid fa-bolt"></i> Execute Simulated ${isLong ? 'LONG BUY' : 'SHORT SELL'} @ 50% MT`;
    }
    
    card.style.display = "block";
}

function dismissReplaySignal() {
    const card = document.getElementById("replaySignalHUD");
    if (card) card.style.display = "none";
}

// ----------------- INTERACTIVE SIMULATION & STEPPED TRAILING SL -----------------

function executeCurrentReplaySignal() {
    if (!replayCurrentSetup) return;
    const setup = replayCurrentSetup;
    
    replaySimTrade = {
        active: true,
        symbol: setup.symbol,
        side: setup.side,
        entryPrice: setup.entryPrice,
        tpPrice: setup.tpPrice,
        slPrice: setup.hardSlPrice,
        hardSlPrice: setup.hardSlPrice,
        softSlPrice: setup.softSlPrice,
        peakRoi: 0.0,
        lockedRoi: 0.0,
        currentStep: 0,
        durationBars: 0,
        filled: true, // filled at MT tap
        fillPrice: setup.entryPrice,
        entryTime: setup.candleTime
    };
    
    dismissReplaySignal();
    updateReplayChartPriceLines();
    renderReplayActiveTradeHUD();
    showOutcomeBanner("⚡ ORDER EXECUTED", `${setup.side === 'BUY' ? 'LONG' : 'SHORT'} 5X Filled @ $${setup.entryPrice.toFixed(4)} (50% MT)`, "info");
    playInstitutionalChime("shield");
}

function updateReplayChartPriceLines() {
    clearReplayChartPriceLines();
    if (!candleSeries || !replaySimTrade) return;
    
    const trade = replaySimTrade;
    try {
        replayPriceLines.entry = candleSeries.createPriceLine({
            price: trade.entryPrice,
            color: '#00DFC0',
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
            title: '50% MT ENTRY'
        });
        
        replayPriceLines.tp = candleSeries.createPriceLine({
            price: trade.tpPrice,
            color: '#00C087',
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Solid,
            axisLabelVisible: true,
            title: 'TP (+14% ROE)'
        });
        
        const isTrailing = (trade.lockedRoi || 0) > 0;
        replayPriceLines.sl = candleSeries.createPriceLine({
            price: trade.slPrice,
            color: isTrailing ? '#FFB800' : '#FF4B55',
            lineWidth: 2,
            lineStyle: isTrailing ? LightweightCharts.LineStyle.Solid : LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
            title: isTrailing ? `ARMOR SL (+${trade.lockedRoi.toFixed(1)}% ROI)` : 'STOP LOSS (-14% ROE)'
        });
    } catch(e) {}
}

function clearReplayChartPriceLines() {
    if (!candleSeries) return;
    try {
        if (replayPriceLines.entry) candleSeries.removePriceLine(replayPriceLines.entry);
        if (replayPriceLines.tp) candleSeries.removePriceLine(replayPriceLines.tp);
        if (replayPriceLines.sl) candleSeries.removePriceLine(replayPriceLines.sl);
        if (replayPriceLines.trailing) candleSeries.removePriceLine(replayPriceLines.trailing);
    } catch(e) {}
    replayPriceLines = { entry: null, tp: null, sl: null, trailing: null };
}

function evaluateActiveReplaySimTrade(candle) {
    if (!replaySimTrade || !replaySimTrade.active) return;
    
    const trade = replaySimTrade;
    const isLong = trade.side === "BUY" || trade.side === "LONG";
    const leverage = 5.0;
    trade.durationBars = (trade.durationBars || 0) + 1;
    
    const barHigh = candle.high;
    const barLow = candle.low;
    const barClose = candle.close;
    
    // Calculate Current Peak ROI
    let currentHighRoi = isLong 
        ? ((barHigh - trade.entryPrice) / trade.entryPrice) * 100 * leverage
        : ((trade.entryPrice - barLow) / trade.entryPrice) * 100 * leverage;
    
    if (currentHighRoi > trade.peakRoi) {
        trade.peakRoi = currentHighRoi;
    }
    
    // Live Bar Close ROE %
    const currRoe = isLong
        ? ((barClose - trade.entryPrice) / trade.entryPrice) * 100 * leverage
        : ((trade.entryPrice - barClose) / trade.entryPrice) * 100 * leverage;
    trade.currRoe = currRoe;
    
    // STEPPED TRAILING SL LADDER (+5% -> +1%, +9.5% -> +5%, +14.5% -> +10%)
    let targetLockedRoi = trade.lockedRoi || 0;
    let targetStep = trade.currentStep || 0;
    
    if (trade.peakRoi >= 5.0 && targetLockedRoi < 1.0) {
        targetLockedRoi = 1.0;
        targetStep = 1;
    }
    if (trade.peakRoi >= 9.5 && targetLockedRoi < 5.0) {
        targetLockedRoi = 5.0;
        targetStep = 2;
    }
    if (trade.peakRoi >= 14.5 && targetLockedRoi < 10.0) {
        targetLockedRoi = 10.0;
        targetStep = 3;
    }
    if (trade.peakRoi >= 19.5 && targetLockedRoi < 15.0) {
        targetLockedRoi = 15.0;
        targetStep = 4;
    }
    if (trade.peakRoi >= 24.5 && targetLockedRoi < 20.0) {
        targetLockedRoi = 20.0;
        targetStep = 5;
    }
    
    if (targetLockedRoi > (trade.lockedRoi || 0)) {
        trade.lockedRoi = targetLockedRoi;
        trade.currentStep = targetStep;
        
        const spotShift = (targetLockedRoi / 100.0) / leverage;
        trade.slPrice = isLong 
            ? trade.entryPrice * (1.0 + spotShift)
            : trade.entryPrice * (1.0 - spotShift);
        
        updateReplayChartPriceLines();
        renderReplayActiveTradeHUD();
        showOutcomeBanner(`🛡️ PROFIT ARMOR STEP ${targetStep}`, `SL Raised to +${targetLockedRoi.toFixed(1)}% ROI Protected`, "shield");
        playInstitutionalChime("shield");
    }
    
    // CHECK TAKE PROFIT HIT (+14.0% ROE)
    const tpHit = isLong ? (barHigh >= trade.tpPrice) : (barLow <= trade.tpPrice);
    if (tpHit) {
        resolveReplayTrade("TAKE_PROFIT", trade.tpPrice, +14.0, candle);
        return;
    }
    
    // CHECK TRAILING STOP LOSS HIT
    if (trade.lockedRoi > 0) {
        const trailingHit = isLong ? (barLow <= trade.slPrice) : (barHigh >= trade.slPrice);
        if (trailingHit) {
            resolveReplayTrade("TRAILING_SL", trade.slPrice, trade.lockedRoi, candle);
            return;
        }
    }
    
    // CHECK INITIAL HARD STOP LOSS HIT (-14.0% ROE)
    const slHit = isLong ? (barLow <= trade.hardSlPrice) : (barHigh >= trade.hardSlPrice);
    if (slHit) {
        resolveReplayTrade("STOP_LOSS", trade.hardSlPrice, -14.0, candle);
        return;
    }
    
    renderReplayActiveTradeHUD();
}

function renderReplayActiveTradeHUD() {
    const hud = document.getElementById("replayActiveTradeHUD");
    if (!hud || !replaySimTrade) return;
    
    const trade = replaySimTrade;
    const isLong = trade.side === "BUY" || trade.side === "LONG";
    
    const b = document.getElementById("rahSideBadge");
    if (b) {
        b.className = `rah-badge ${isLong ? 'rah-long' : 'rah-short'}`;
        b.innerText = `${isLong ? 'LONG' : 'SHORT'} 5X (SIM)`;
    }
    
    const ep = document.getElementById("rahEntry");
    if (ep) ep.innerText = `$${trade.entryPrice.toFixed(4)}`;
    
    const curP = replayCandles && replayIndex > 0 ? replayCandles[replayIndex - 1].close : trade.entryPrice;
    const cur = document.getElementById("rahCurrent");
    if (cur) cur.innerText = `$${curP.toFixed(4)}`;
    
    const roeEl = document.getElementById("rahRoe");
    if (roeEl) {
        const roe = trade.currRoe || 0.0;
        roeEl.className = roe >= 0 ? "val-green" : "val-red";
        roeEl.innerText = `${roe >= 0 ? '+' : ''}${roe.toFixed(2)}%`;
    }
    
    const pkEl = document.getElementById("rahPeakRoi");
    if (pkEl) pkEl.innerText = `+${(trade.peakRoi || 0).toFixed(1)}%`;
    
    const armEl = document.getElementById("rahArmorStatus");
    if (armEl) {
        if (trade.currentStep > 0) {
            armEl.innerHTML = `<span style="color:var(--gold); font-weight:800;">Step ${trade.currentStep}: +${trade.lockedRoi.toFixed(1)}% Locked</span>`;
        } else {
            armEl.innerText = "Initial Shield (-14% ROE)";
        }
    }
    
    hud.style.display = "block";
}

function closeReplayTradeManual() {
    if (!replaySimTrade) return;
    const curP = replayCandles && replayIndex > 0 ? replayCandles[replayIndex - 1].close : replaySimTrade.entryPrice;
    const curC = replayCandles && replayIndex > 0 ? replayCandles[replayIndex - 1] : { time: Math.floor(Date.now() / 1000) };
    resolveReplayTrade("MANUAL_EXIT", curP, replaySimTrade.currRoe || 0.0, curC);
}

function resolveReplayTrade(outcome, exitPrice, roePct, candle) {
    if (!replaySimTrade) return;
    const trade = replaySimTrade;
    const pnlUsdt = 50.0 * (roePct / 100.0);
    
    const record = {
        id: replaySimJournal.length + 1,
        symbol: currentSymbol,
        side: trade.side === "BUY" ? "LONG" : "SHORT",
        entryPrice: trade.entryPrice,
        exitPrice: exitPrice,
        outcome: outcome,
        roePct: roePct,
        pnlUsdt: pnlUsdt,
        lockedRoi: trade.lockedRoi || 0,
        durationBars: trade.durationBars || 1,
        exitTime: candle.time
    };
    
    replaySimJournal.unshift(record);
    updateReplayJournalBadge();
    
    if (outcome === "TAKE_PROFIT") {
        showOutcomeBanner("🏆 TAKE PROFIT REACHED!", `+${roePct.toFixed(2)}% ROE (+$${pnlUsdt.toFixed(2)}) Target Hit!`, "win");
        playInstitutionalChime("win");
    } else if (outcome === "TRAILING_SL") {
        showOutcomeBanner("🛡️ TRAILING SL SECURED!", `+${roePct.toFixed(2)}% ROE Profit Protected (+$${pnlUsdt.toFixed(2)})`, "win");
        playInstitutionalChime("shield");
    } else if (outcome === "STOP_LOSS") {
        showOutcomeBanner("🛑 STOP LOSS HIT", `${roePct.toFixed(2)}% ROE (-$${Math.abs(pnlUsdt).toFixed(2)}) Defense Triggered`, "loss");
    } else {
        showOutcomeBanner("⚡ MANUAL EXIT", `${roePct >= 0 ? '+' : ''}${roePct.toFixed(2)}% ROE ($${pnlUsdt.toFixed(2)})`, "info");
    }
    
    replaySimTrade = null;
    clearReplayChartPriceLines();
    const hud = document.getElementById("replayActiveTradeHUD");
    if (hud) hud.style.display = "none";
}

function showOutcomeBanner(title, subtitle, type = "win") {
    const banner = document.getElementById("replayOutcomeBanner");
    if (!banner) return;
    
    banner.className = `replay-outcome-banner ${type}`;
    const t = document.getElementById("replayOutcomeTitle");
    if (t) t.innerText = title;
    const s = document.getElementById("replayOutcomeSubtitle");
    if (s) s.innerText = subtitle;
    
    const ic = document.getElementById("replayOutcomeIcon");
    if (ic) {
        if (type === "win") ic.innerHTML = '<i class="fa-solid fa-trophy"></i>';
        else if (type === "shield") ic.innerHTML = '<i class="fa-solid fa-shield-halved"></i>';
        else if (type === "loss") ic.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
        else ic.innerHTML = '<i class="fa-solid fa-bolt"></i>';
    }
    
    banner.style.display = "flex";
    if (bannerTimeout) clearTimeout(bannerTimeout);
    bannerTimeout = setTimeout(() => {
        banner.style.display = "none";
    }, 2800);
}

function playInstitutionalChime(type = "signal") {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        
        if (type === "win") {
            osc.frequency.setValueAtTime(587.33, ctx.currentTime);
            osc.frequency.setValueAtTime(880.00, ctx.currentTime + 0.12);
            gain.gain.setValueAtTime(0.12, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.38);
            osc.start();
            osc.stop(ctx.currentTime + 0.38);
        } else if (type === "shield") {
            osc.frequency.setValueAtTime(440, ctx.currentTime);
            osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.1);
            gain.gain.setValueAtTime(0.1, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
            osc.start();
            osc.stop(ctx.currentTime + 0.3);
        } else {
            osc.frequency.setValueAtTime(523.25, ctx.currentTime);
            gain.gain.setValueAtTime(0.1, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
            osc.start();
            osc.stop(ctx.currentTime + 0.25);
        }
    } catch(e) {}
}

// ----------------- REPLAY BACKTEST JOURNAL -----------------

function updateReplayJournalBadge() {
    const el = document.getElementById("replayJournalBadgeCount");
    if (el) el.innerText = replaySimJournal.length;
}

function openReplayJournalModal() {
    renderReplayJournalTable();
    const m = document.getElementById("replayJournalModal");
    if (m) m.style.display = "flex";
}

function closeReplayJournalModal() {
    const m = document.getElementById("replayJournalModal");
    if (m) m.style.display = "none";
}

function clearReplayJournal() {
    if (confirm("Reset Replay Backtest Journal and start fresh?")) {
        replaySimJournal = [];
        updateReplayJournalBadge();
        renderReplayJournalTable();
    }
}

function renderReplayJournalTable() {
    const total = replaySimJournal.length;
    const wins = replaySimJournal.filter(x => x.roePct > 0).length;
    const losses = replaySimJournal.filter(x => x.roePct < 0).length;
    const winRate = total > 0 ? ((wins / total) * 100).toFixed(1) : "0.0";
    const netReturn = replaySimJournal.reduce((acc, x) => acc + x.roePct, 0);
    
    const totEl = document.getElementById("rjmTotalTrades");
    if (totEl) totEl.innerText = total;
    const wrEl = document.getElementById("rjmWinRate");
    if (wrEl) wrEl.innerText = `${winRate}%`;
    const wEl = document.getElementById("rjmWins");
    if (wEl) wEl.innerText = wins;
    const lEl = document.getElementById("rjmLosses");
    if (lEl) lEl.innerText = losses;
    const netEl = document.getElementById("rjmNetReturn");
    if (netEl) {
        netEl.className = `rjm-stat-val ${netReturn >= 0 ? 'val-green' : 'val-red'}`;
        netEl.innerText = `${netReturn >= 0 ? '+' : ''}${netReturn.toFixed(2)}%`;
    }
    
    const tbody = document.getElementById("rjmTableBody");
    if (!tbody) return;
    
    if (replaySimJournal.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding:20px;">No trades simulated yet. Run Bar Replay to trigger Hermes 3.0 setups!</td></tr>';
        return;
    }
    
    tbody.innerHTML = replaySimJournal.map((t, idx) => {
        const isWin = t.roePct > 0;
        const outcomeBadge = t.outcome === "TAKE_PROFIT" 
            ? '<span style="color:var(--buy-green); font-weight:800;">🏆 TP HIT (+14%)</span>'
            : (t.outcome === "TRAILING_SL" 
                ? `<span style="color:var(--gold); font-weight:800;">🛡️ TRAIL SL (+${t.lockedRoi}%)</span>`
                : (t.outcome === "STOP_LOSS" 
                    ? '<span style="color:var(--sell-red); font-weight:800;">🛑 SL HIT (-14%)</span>' 
                    : '<span style="color:#94A3B8;">⚡ MANUAL</span>'));
        
        return `
            <tr>
                <td style="color:var(--text-muted);">${total - idx}</td>
                <td><span style="font-weight:800; color:${t.side === 'LONG' ? 'var(--buy-green)' : 'var(--sell-red)'};">${t.side}</span></td>
                <td style="color:var(--brand-teal); font-weight:700;">$${t.entryPrice.toFixed(4)}</td>
                <td style="color:#fff;">$${t.exitPrice.toFixed(4)}</td>
                <td>${outcomeBadge}</td>
                <td style="font-weight:800; color:${isWin ? 'var(--buy-green)' : 'var(--sell-red)'};">${t.roePct >= 0 ? '+' : ''}${t.roePct.toFixed(2)}%</td>
                <td style="font-weight:800; color:${t.pnlUsdt >= 0 ? 'var(--buy-green)' : 'var(--sell-red)'};">${t.pnlUsdt >= 0 ? '+' : ''}$${t.pnlUsdt.toFixed(2)}</td>
                <td style="color:var(--text-muted);">${t.durationBars} bars</td>
            </tr>
        `;
    }).join("");
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
