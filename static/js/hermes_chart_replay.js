/**
 * HERMES 3.5 RADAR HARVEST INTERACTIVE BAR REPLAY & STRATEGY BACKTESTER SUITE
 * =====================================================================
 * Pure Candlesticks (EMA lines & Volume removed as requested by user).
 * Full Hermes 3.5 Radar Harvest Strategy Detection, Entry/TP/SL Markers & Lines.
 * Live Open Position Synchronization & Historical Replay Forensics.
 * Force-Landscape Fullscreen Mode with Mobile Optimization.
 */

(function(window) {
    'use strict';

    let mChart = null;
    let mCandleSeries = null;
    let mSymbol = "BTCUSDT";
    let mInterval = "15m";
    let mFullCandles = [];

    // Strategy & Markers State
    let mActiveLivePosition = null;
    let mDetectedSetups = []; // All historical setups
    let mCurrentMarkers = [];

    // Replay State
    let mIsReplayMode = false;
    let mReplayCandles = [];
    let mReplayIndex = 0;
    let mReplayTimer = null;
    let mReplaySpeedMs = 800;
    let mIsHermesStratActive = true;
    let mIsAutoTrade = false;

    // Simulation State
    let mSimTrade = null;
    let mCurrentSetup = null;
    let mSimJournal = [];
    let mPriceLines = { entry: null, tp: null, sl: null, liveEntry: null, liveTp: null, liveSl: null };
    let mBannerTimeout = null;

    // Measure Tool State
    let mIsMeasureActive = false;
    let mIsMeasuring = false;
    let mDraggingHandle = null;
    let mMeasurePt1 = null;
    let mMeasurePt2 = null;

    // Landscape Fullscreen State
    let mIsLandscape = false;
    let mCountdownTimerInterval = null;

    // -------------------------------------------------------------
    // LIVE CANDLE COUNTDOWN TIMER (Item 2)
    // -------------------------------------------------------------
    function startLiveCountdownTimer() {
        if (mCountdownTimerInterval) clearInterval(mCountdownTimerInterval);
        updateLiveCountdownTimer();
        mCountdownTimerInterval = setInterval(updateLiveCountdownTimer, 1000);
    }

    function updateLiveCountdownTimer() {
        const timerEl = document.getElementById("mCandleCountdownTimer");
        if (!timerEl) return;

        const nowSec = Math.floor(Date.now() / 1000);
        let intervalSec = 900;
        const tf = (mInterval || '15m').toLowerCase();
        if (tf.includes('1m') && !tf.includes('15m')) intervalSec = 60;
        else if (tf.includes('3m')) intervalSec = 180;
        else if (tf.includes('5m')) intervalSec = 300;
        else if (tf.includes('15m')) intervalSec = 900;
        else if (tf.includes('30m')) intervalSec = 1800;
        else if (tf.includes('1h')) intervalSec = 3600;
        else if (tf.includes('2h')) intervalSec = 7200;
        else if (tf.includes('4h')) intervalSec = 14400;
        else if (tf.includes('6h')) intervalSec = 21600;
        else if (tf.includes('8h')) intervalSec = 28800;
        else if (tf.includes('12h')) intervalSec = 43200;
        else if (tf.includes('1d')) intervalSec = 86400;
        else if (tf.includes('1w')) intervalSec = 604800;

        const rem = intervalSec - (nowSec % intervalSec);
        const hrs = Math.floor(rem / 3600);
        const mins = Math.floor((rem % 3600) / 60);
        const secs = rem % 60;

        const timerStr = hrs > 0 
            ? `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
            : `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        timerEl.innerText = timerStr;
    }

    // -------------------------------------------------------------
    // INITIALIZATION & PURE CANDLESTICK CHART SETUP
    // -------------------------------------------------------------

    function initHermesChart(containerId = "mobileChartCanvas", defaultSymbol = "BTCUSDT") {
        mSymbol = defaultSymbol.toUpperCase();
        const container = document.getElementById(containerId);
        if (!container || !window.LightweightCharts) return;

        if (mChart) {
            try { mChart.remove(); } catch(e) {}
            mChart = null;
        }

        container.innerHTML = "";

        // PURE CANDLESTICK CHART (NO EMA LINES, NO VOLUME SERIES)
        mChart = window.LightweightCharts.createChart(container, {
            width: container.clientWidth || 360,
            height: container.clientHeight || 480,
            layout: {
                background: { type: 'solid', color: '#0B0E14' },
                textColor: '#94A3B8',
                fontSize: 11,
                fontFamily: "'JetBrains Mono', -apple-system, sans-serif"
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.04)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.04)' }
            },
            crosshair: {
                mode: window.LightweightCharts.CrosshairMode.Normal,
                vertLine: {
                    color: 'rgba(255, 255, 255, 0.45)',
                    width: 1,
                    style: 2,
                    visible: true,
                    labelVisible: true,
                    labelBackgroundColor: '#1E293B'
                },
                horzLine: {
                    color: 'rgba(255, 255, 255, 0.45)',
                    width: 1,
                    style: 2,
                    visible: true,
                    labelVisible: true,
                    labelBackgroundColor: '#1E293B'
                }
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.08)',
                autoScale: true,
                scaleMargins: { top: 0.10, bottom: 0.10 },
                alignLabels: true
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.08)',
                timeVisible: true,
                secondsVisible: false,
                rightOffset: 18,
                barSpacing: 9,
                minBarSpacing: 3,
                fixLeftEdge: false,
                fixRightEdge: false
            }
        });

        // Candlestick Series - full height, sharp institutional theme
        mCandleSeries = mChart.addCandlestickSeries({
            upColor: '#00C087',
            downColor: '#FF4B55',
            borderUpColor: '#00C087',
            borderDownColor: '#FF4B55',
            wickUpColor: '#00C087',
            wickDownColor: '#FF4B55'
        });

        // Crosshair OHLC header update
        mChart.subscribeCrosshairMove(param => {
            if (!param || !param.time || !param.seriesPrices) return;
            const bar = param.seriesPrices.get(mCandleSeries);
            if (bar) updateChartHeaderOHLC(bar);
        });

        // Debounced redraw of Hermes 3.5 Order Block Boxes during pan & zoom
        mChart.timeScale().subscribeVisibleLogicalRangeChange(() => {
            drawMobileHermes35Boxes();
        });

        // ResizeObserver
        const ro = new ResizeObserver(entries => {
            if (!entries || !entries.length || !mChart) return;
            const { width, height } = entries[0].contentRect;
            mChart.applyOptions({ width: Math.max(width, 280), height: Math.max(height, 260) });
        });
        ro.observe(container);

        initMeasureToolOverlay();
        startLiveCountdownTimer();
        fetchLivePositionAndLoad();
    }

    async function fetchLivePositionAndLoad() {
        // 1. Fetch live open positions from DB (checking both paper & trade endpoints)
        try {
            let found = null;
            const posRes = await fetch(`/api/paper/positions?t=${Date.now()}`);
            if (posRes.ok) {
                const posData = await posRes.json();
                const list = posData.positions || [];
                found = list.find(p => (p.symbol || '').toUpperCase() === mSymbol.toUpperCase()) || null;
            }
            if (!found) {
                const trRes = await fetch(`/api/trade/positions?t=${Date.now()}`);
                if (trRes.ok) {
                    const trData = await trRes.json();
                    const list = trData.positions || [];
                    found = list.find(p => (p.symbol || '').toUpperCase() === mSymbol.toUpperCase()) || null;
                }
            }
            mActiveLivePosition = found;
        } catch(e) {
            mActiveLivePosition = null;
        }

        // 2. Fetch candles
        await loadKlinesData();
    }

    async function loadKlinesData() {
        if (!mCandleSeries) return;
        try {
            const res = await fetch(`/api/klines/${mSymbol}?interval=${mInterval}&limit=180&t=${Date.now()}`);
            if (!res.ok) return;
            const data = await res.json();
            if (!data || !data.candles || !data.candles.length) return;

            mFullCandles = data.candles;
            mCandleSeries.setData(mFullCandles);

            // Item 5: Dynamic 4-decimal precision for sub-dollar coins (e.g. WLD, PEPE, DOGE)
            if (mFullCandles.length > 0) {
                const lastClose = mFullCandles[mFullCandles.length - 1].close;
                const precision = lastClose < 0.1 ? 6 : (lastClose < 1 ? 4 : (lastClose < 10 ? 3 : 2));
                const minMove = Number((1 / Math.pow(10, precision)).toFixed(precision));
                mCandleSeries.applyOptions({
                    priceFormat: {
                        type: 'price',
                        precision: precision,
                        minMove: minMove
                    }
                });
            }

            // Hermes 3.5 Radar Harvest Single Tier Zones from Backend Engine
            if (data.zones && data.zones.length > 0) {
                mDetectedSetups = data.zones.map(z => {
                    const oTime = z.origin_time > 1e11 ? Math.floor(z.origin_time / 1000) : z.origin_time;
                    const fTime = z.fill_time ? (z.fill_time > 1e11 ? Math.floor(z.fill_time / 1000) : z.fill_time) : oTime;
                    return {
                        ...z,
                        candleTime: fTime,
                        originTime: oTime,
                        entryPrice: z.entry_price || z.ob_high,
                        radarPrice: z.radar_price,
                        tpPrice: z.tp_price,
                        slPrice: z.sl_price,
                        side: (z.side || 'BUY').toUpperCase()
                    };
                });
            } else {
                mDetectedSetups = scanAllHermes30Setups(mFullCandles);
            }

            // Update markers on chart
            updateChartMarkers();

            // Render live position lines if active
            renderLivePositionLines();

            if (mFullCandles.length > 0) {
                updateChartHeaderOHLC(mFullCandles[mFullCandles.length - 1]);
            }

            // Item 8: Right Breathing Space with 100% Guaranteed Visible Candles
            mChart.timeScale().applyOptions({ rightOffset: 18 });
            mChart.timeScale().fitContent();

            // Item 11: Top Header Strip & Search Bar Sync
            const symEl = document.getElementById("mobileChartSymbolText");
            if (symEl) symEl.innerText = mSymbol;
            const tvSym = document.getElementById("mTvHeaderSymbol");
            if (tvSym) tvSym.innerText = mSymbol.replace('USDT', '') + ' / USDT';
            const tvTf = document.getElementById("mTvHeaderTf");
            if (tvTf) tvTf.innerText = mInterval.toUpperCase();
            const searchInput = document.getElementById("mobileChartCoinSearch");
            if (searchInput && !searchInput.matches(':focus')) searchInput.value = mSymbol;
            const tradeSym = document.getElementById("tradeSymbol");
            if (tradeSym) tradeSym.innerText = mSymbol;

            const priceEl = document.getElementById("mobileChartPriceText");
            if (priceEl && mFullCandles.length > 0) {
                const last = mFullCandles[mFullCandles.length - 1];
                const dec = last.close < 0.1 ? 6 : (last.close < 1 ? 4 : (last.close < 10 ? 3 : 2));
                priceEl.innerText = `$${last.close.toFixed(dec)}`;
            }
        } catch(e) {
            console.warn("Mobile klines load error:", e);
        }
    }

    function updateChartHeaderOHLC(bar) {
        if (!bar) return;
        const oEl = document.getElementById("mOhlcO");
        const hEl = document.getElementById("mOhlcH");
        const lEl = document.getElementById("mOhlcL");
        const cEl = document.getElementById("mOhlcC");
        const chgEl = document.getElementById("mOhlcChg");

        const o = bar.open || 0;
        const h = bar.high || 0;
        const l = bar.low || 0;
        const c = bar.close || 0;
        const chg = o > 0 ? ((c - o) / o) * 100 : 0;
        const dec = c < 0.1 ? 6 : (c < 1 ? 4 : (c < 10 ? 3 : 2));

        if (oEl) oEl.innerText = o.toFixed(dec);
        if (hEl) hEl.innerText = h.toFixed(dec);
        if (lEl) lEl.innerText = l.toFixed(dec);
        if (cEl) {
            cEl.innerText = c.toFixed(dec);
            cEl.style.color = chg >= 0 ? '#00C087' : '#FF4B55';
        }
        if (chgEl) {
            chgEl.innerText = `${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%`;
            chgEl.style.color = chg >= 0 ? '#00C087' : '#FF4B55';
        }
    }

    function setMobileTimeframe(tf, btn) {
        mInterval = tf;
        document.querySelectorAll(".m-tf-btn").forEach(b => b.classList.remove("active"));
        if (btn) btn.classList.add("active");
        const tvTf = document.getElementById("mTvHeaderTf");
        if (tvTf) tvTf.innerText = tf.toUpperCase();
        if (mIsReplayMode) exitMobileReplay();
        loadKlinesData();
        updateLiveCountdownTimer();
    }

    function setMobileSymbol(sym) {
        mSymbol = sym.toUpperCase();
        const tvSym = document.getElementById("mTvHeaderSymbol");
        if (tvSym) tvSym.innerText = mSymbol.replace('USDT', '') + ' / USDT';
        const searchInput = document.getElementById("mobileChartCoinSearch");
        if (searchInput) searchInput.value = mSymbol;
        const tradeSym = document.getElementById("tradeSymbol");
        if (tradeSym) tradeSym.innerText = mSymbol;
        if (mIsReplayMode) exitMobileReplay();
        fetchLivePositionAndLoad();
    }

    // -------------------------------------------------------------
    // HERMES 3.5 RADAR HARVEST COMPREHENSIVE SETUPS SCANNER & MARKERS
    // -------------------------------------------------------------

    // -------------------------------------------------------------
    // HERMES 3.5 RADAR HARVEST SINGLE TIER ENGINE (100% PINE SCRIPT V5 PARITY)
    // -------------------------------------------------------------

    function scanAllHermes30Setups(candles) {
        // Pure Hermes 3.5 Radar Harvest Scanner: 5% Boundary Penetration + 0.20% Radar
        const setups = [];
        if (!candles || candles.length < 25) return setups;

        const tf = (mInterval || '15m').toLowerCase();
        const minDisp = (tf === '15m' || tf === '1h') ? 0.035 : 0.05;
        const n = candles.length;

        for (let i = 15; i < n - 3; i++) {
            const c3 = candles[i];
            const c2 = candles[i + 1];
            const c1 = candles[i + 2];

            const impulseH = Math.max(c1.high, c2.high);
            const impulseL = Math.min(c1.low, c2.low);

            // 1. BULLISH DEMAND SETUP (5% Boundary)
            const isRed = c3.close < c3.open;
            const hasBullFvg = c1.low > c3.high;
            const bullDisp = c3.low > 0 ? ((impulseH - c3.low) / c3.low) : 0;

            if (isRed && hasBullFvg && bullDisp >= minDisp) {
                const oHigh = c3.high;
                const oLow = c3.low;
                const oRng = oHigh - oLow;
                if (oRng > 0) {
                    const entP = Number((oHigh - (oRng * 0.05)).toFixed(8));
                    const radP = Number((entP * 1.0020).toFixed(8));
                    const tpP = Number((entP * (1.0 + 0.0280)).toFixed(8));
                    const slP = Number((entP * (1.0 - 0.0280)).toFixed(8));

                    // Search for first mitigation tap
                    for (let k = i + 3; k < n; k++) {
                        const bar = candles[k];
                        if (bar.low <= entP && bar.low >= slP) {
                            setups.push({
                                symbol: mSymbol,
                                side: "BUY",
                                type: "LONG",
                                ob_high: oHigh,
                                ob_low: oLow,
                                entry_price: entP,
                                entryPrice: entP,
                                radar_price: radP,
                                radarPrice: radP,
                                tp_price: tpP,
                                tpPrice: tpP,
                                sl_price: slP,
                                slPrice: slP,
                                origin_time: c3.time,
                                originTime: c3.time,
                                fill_time: bar.time,
                                candleTime: bar.time,
                                candleIndex: k,
                                status: "ACTIVE_TAPPED",
                                runway_pct: 22,
                                bars_alive: k - i
                            });
                            break;
                        }
                    }
                }
            }

            // 2. BEARISH SUPPLY SETUP (5% Boundary)
            const isGreen = c3.close > c3.open;
            const hasBearFvg = c1.high < c3.low;
            const bearDisp = c3.high > 0 ? ((c3.high - impulseL) / c3.high) : 0;

            if (isGreen && hasBearFvg && bearDisp >= minDisp) {
                const oHigh = c3.high;
                const oLow = c3.low;
                const oRng = oHigh - oLow;
                if (oRng > 0) {
                    const entP = Number((oLow + (oRng * 0.05)).toFixed(8));
                    const radP = Number((entP * 0.9980).toFixed(8));
                    const tpP = Number((entP * (1.0 - 0.0280)).toFixed(8));
                    const slP = Number((entP * (1.0 + 0.0280)).toFixed(8));

                    for (let k = i + 3; k < n; k++) {
                        const bar = candles[k];
                        if (bar.high >= entP && bar.high <= slP) {
                            setups.push({
                                symbol: mSymbol,
                                side: "SELL",
                                type: "SHORT",
                                ob_high: oHigh,
                                ob_low: oLow,
                                entry_price: entP,
                                entryPrice: entP,
                                radar_price: radP,
                                radarPrice: radP,
                                tp_price: tpP,
                                tpPrice: tpP,
                                sl_price: slP,
                                slPrice: slP,
                                origin_time: c3.time,
                                originTime: c3.time,
                                fill_time: bar.time,
                                candleTime: bar.time,
                                candleIndex: k,
                                status: "ACTIVE_TAPPED",
                                runway_pct: 22,
                                bars_alive: k - i
                            });
                            break;
                        }
                    }
                }
            }
        }
        return setups;
    }

    // -------------------------------------------------------------
    // HTML5 CANVAS OVERLAY: TRANSLUCENT DEMAND/SUPPLY BOXES & RADAR LINES
    // -------------------------------------------------------------

    function getMobileOverlayCanvas() {
        const container = document.getElementById("mobileChartCanvas");
        if (!container) return null;

        let canvas = document.getElementById("mobileChartOverlayCanvas");
        if (!canvas) {
            canvas = document.createElement("canvas");
            canvas.id = "mobileChartOverlayCanvas";
            canvas.style.position = "absolute";
            canvas.style.top = "0";
            canvas.style.left = "0";
            canvas.style.pointerEvents = "none";
            canvas.style.zIndex = "10";
            container.appendChild(canvas);
        }

        const dpr = window.devicePixelRatio || 1;
        const w = container.clientWidth || 360;
        const h = container.clientHeight || 340;

        const targetW = Math.floor(w * dpr);
        const targetH = Math.floor(h * dpr);
        if (!canvas.width || Math.abs(canvas.width - targetW) >= 4 || Math.abs(canvas.height - targetH) >= 4) {
            canvas.width = targetW;
            canvas.height = targetH;
            canvas.style.width = w + "px";
            canvas.style.height = h + "px";
        }

        const ctx = canvas.getContext("2d");
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        return { canvas, ctx, width: w, height: h };
    }

    function drawMobileHermes35Boxes() {
        const overlay = getMobileOverlayCanvas();
        if (!overlay) return;
        const { ctx, width, height } = overlay;
        ctx.clearRect(0, 0, width, height);

        if (!mChart || !mCandleSeries || !mDetectedSetups || mDetectedSetups.length === 0) {
            return;
        }

        const timeScale = mChart.timeScale();
        const visibleRange = timeScale.getVisibleRange();
        const plotWidth = width - 55;
        const lastCandle = mFullCandles && mFullCandles.length > 0 ? mFullCandles[mFullCandles.length - 1] : null;
        const lastCandleX = lastCandle ? timeScale.timeToCoordinate(lastCandle.time) : null;

        mDetectedSetups.forEach(z => {
            if (!z.ob_high || !z.ob_low) return;
            const isBuySide = (z.side === 'BUY' || z.side === 'LONG');
            const originSec = z.origin_time > 1e11 ? Math.floor(z.origin_time / 1000) : (z.originTime || z.candleTime);
            if (!originSec) return;

            // Item 6: Detect if historical zone is mitigated / completed
            const isMitigated = Boolean(
                z.status === 'MITIGATED' || 
                z.status === 'BROKEN' || 
                z.completed === true || 
                (z.fill_time && lastCandle && z.fill_time < lastCandle.time && z.status !== 'ACTIVE_PENDING')
            );

            let endSec = z.end_time ? (z.end_time > 1e11 ? Math.floor(z.end_time / 1000) : z.end_time) : null;
            if (!endSec && z.fill_time) endSec = z.fill_time > 1e11 ? Math.floor(z.fill_time / 1000) : z.fill_time;

            let x1 = timeScale.timeToCoordinate(originSec);
            if (x1 === null || x1 === undefined) {
                if (visibleRange && originSec < visibleRange.from) x1 = 0;
                else return;
            } else {
                x1 = Math.max(0, x1);
            }

            // Item 3: Order Block Future Extension into empty space (TradingView Parity)
            let x2 = plotWidth;
            if (isMitigated && endSec) {
                const coordEnd = timeScale.timeToCoordinate(endSec);
                if (coordEnd !== null && coordEnd !== undefined) {
                    x2 = Math.max(x1 + 6, Math.min(plotWidth, coordEnd));
                }
            } else {
                // UNMITIGATED ACTIVE ZONE: Project forward ~18 bars ahead of current candle into rightOffset airspace
                if (lastCandleX !== null && lastCandleX !== undefined) {
                    x2 = Math.min(plotWidth, lastCandleX + 18 * 8);
                } else {
                    x2 = plotWidth;
                }
            }

            const boxWidth = x2 - x1;
            if (boxWidth <= 3) return;

            const yTop = mCandleSeries.priceToCoordinate(Math.max(z.ob_high, z.ob_low));
            const yBottom = mCandleSeries.priceToCoordinate(Math.min(z.ob_high, z.ob_low));
            if (yTop === null || yBottom === null) return;

            const minY = Math.min(yTop, yBottom);
            const maxY = Math.max(yTop, yBottom);
            const boxHeight = Math.max(3, maxY - minY);

            const obRange = Math.abs(z.ob_high - z.ob_low);
            const entPx = z.entry_price || (isBuySide ? (z.ob_high - obRange * 0.05) : (z.ob_low + obRange * 0.05));
            const radPx = z.radar_price || (isBuySide ? entPx * 1.0020 : entPx * 0.9980);

            // Item 6: Purane Mitigated Boxes ka Fade (80% opacity reduction & faint dotted border)
            ctx.save();
            if (isMitigated) {
                ctx.fillStyle = isBuySide ? 'rgba(0, 245, 155, 0.03)' : 'rgba(255, 59, 105, 0.03)';
                ctx.fillRect(x1, minY, boxWidth, boxHeight);
                ctx.strokeStyle = isBuySide ? 'rgba(0, 245, 155, 0.18)' : 'rgba(255, 59, 105, 0.18)';
                ctx.lineWidth = 1.0;
                ctx.setLineDash([3, 4]);
                ctx.strokeRect(x1, minY, boxWidth, boxHeight);
            } else {
                // Fresh Active Order Block Box
                ctx.fillStyle = isBuySide ? 'rgba(0, 245, 155, 0.16)' : 'rgba(255, 59, 105, 0.16)';
                ctx.fillRect(x1, minY, boxWidth, boxHeight);
                ctx.strokeStyle = isBuySide ? 'rgba(0, 245, 155, 0.65)' : 'rgba(255, 59, 105, 0.65)';
                ctx.lineWidth = 1.3;
                ctx.setLineDash([]);
                ctx.strokeRect(x1, minY, boxWidth, boxHeight);
            }
            ctx.restore();

            // 2. 5% Boundary Penetration Line (Amber Gold #F59E0B dashed)
            const yEnt = mCandleSeries.priceToCoordinate(entPx);
            if (yEnt !== null && !isNaN(yEnt)) {
                ctx.save();
                ctx.strokeStyle = isMitigated ? 'rgba(245, 158, 11, 0.25)' : '#F59E0B';
                ctx.lineWidth = isMitigated ? 0.8 : 1.2;
                ctx.setLineDash([4, 3]);
                ctx.beginPath();
                ctx.moveTo(x1, yEnt);
                ctx.lineTo(x2, yEnt);
                ctx.stroke();
                ctx.restore();
            }

            // 3. 0.20% Proximity Radar Line (Cyan #38BDF8 dotted)
            const yRad = mCandleSeries.priceToCoordinate(radPx);
            if (yRad !== null && !isNaN(yRad)) {
                ctx.save();
                ctx.strokeStyle = isMitigated ? 'rgba(56, 189, 248, 0.25)' : 'rgba(56, 189, 248, 0.90)';
                ctx.lineWidth = 1.0;
                ctx.setLineDash([2, 3]);
                ctx.beginPath();
                ctx.moveTo(x1, yRad);
                ctx.lineTo(x2, yRad);
                ctx.stroke();
                ctx.restore();
            }
        });
    }

    // -------------------------------------------------------------
    // PURE HERMES 3.5 MARKERS (NO NOISE, NO EXTRA ARROWS)
    // -------------------------------------------------------------

    function updateChartMarkers() {
        if (!mCandleSeries) return;
        mCurrentMarkers = [];
        mCandleSeries.setMarkers([]);
        drawMobileHermes35Boxes();
    }

    // -------------------------------------------------------------
    // PURE HERMES 3.5 PRICE AXIS LEVELS (ONLY ACTIVE SETUP LEVELS)
    // -------------------------------------------------------------

    function renderLivePositionLines() {
        // Zero noise: clear infinite price lines so chart matches pure TradingView canvas
        clearLivePositionLines();
        drawMobileHermes35Boxes();
    }

    function clearLivePositionLines() {
        if (!mCandleSeries) return;
        try {
            if (mPriceLines.liveEntry) mCandleSeries.removePriceLine(mPriceLines.liveEntry);
            if (mPriceLines.liveTp) mCandleSeries.removePriceLine(mPriceLines.liveTp);
            if (mPriceLines.liveSl) mCandleSeries.removePriceLine(mPriceLines.liveSl);
            if (mPriceLines.entry) mCandleSeries.removePriceLine(mPriceLines.entry);
            if (mPriceLines.tp) mCandleSeries.removePriceLine(mPriceLines.tp);
            if (mPriceLines.sl) mCandleSeries.removePriceLine(mPriceLines.sl);
        } catch(e) {}
        mPriceLines.liveEntry = null;
        mPriceLines.liveTp = null;
        mPriceLines.liveSl = null;
        mPriceLines.entry = null;
        mPriceLines.tp = null;
        mPriceLines.sl = null;
    }

    function renderLivePositionHUD() {
        const hud = document.getElementById("mobileReplayActiveHUD");
        if (!hud) return;

        if (!mActiveLivePosition && (!mSimTrade || !mSimTrade.active)) {
            hud.style.display = "none";
            return;
        }

        if (mSimTrade && mSimTrade.active) {
            renderReplayActiveHUD();
            return;
        }

        const p = mActiveLivePosition;
        const isLong = (p.side || '').toUpperCase() === 'BUY' || (p.side_raw || '').toUpperCase() === 'LONG';

        const b = document.getElementById("mRahSide");
        if (b) {
            b.className = `rah-badge ${isLong ? 'rah-long' : 'rah-short'}`;
            b.innerText = `${isLong ? 'LONG' : 'SHORT'} 5X (LIVE)`;
        }

        const ep = document.getElementById("mRahEntry");
        if (ep) ep.innerText = `$${(p.entry_price || 0).toFixed(p.entry_price < 1 ? 4 : 2)}`;

        const curP = p.mark_price || p.current_price || (mFullCandles.length > 0 ? mFullCandles[mFullCandles.length - 1].close : p.entry_price);
        const cur = document.getElementById("mRahCur");
        if (cur) cur.innerText = `$${curP.toFixed(curP < 1 ? 4 : 2)}`;

        const roeEl = document.getElementById("mRahRoe");
        if (roeEl) {
            const roe = p.pnl_pct || p.roi_pct || 0;
            roeEl.className = roe >= 0 ? "val-green" : "val-red";
            roeEl.innerText = p.roe_str || `${roe >= 0 ? '+' : ''}${roe.toFixed(2)}%`;
        }

        const pkEl = document.getElementById("mRahPeak");
        if (pkEl) pkEl.innerText = `+${(p.mfe_pct || 0).toFixed(1)}%`;

        const armEl = document.getElementById("mRahArmor");
        if (armEl) {
            if (p.trailing_sl_price && p.trailing_sl_price > 0) {
                armEl.innerHTML = `<span style="color:var(--gold); font-weight:800;">🛡️ Armor Active: SL @ $${p.trailing_sl_price}</span>`;
            } else {
                armEl.innerText = "Initial Shield (-14% ROE)";
            }
        }

        hud.style.display = "block";
    }

    // -------------------------------------------------------------
    // FREE HISTORICAL BAR REPLAY SIMULATOR
    // -------------------------------------------------------------

    function toggleMobileReplay() {
        if (mIsReplayMode) {
            exitMobileReplay();
        } else {
            startMobileReplay();
        }
    }

    function startMobileReplay() {
        if (!mFullCandles || mFullCandles.length < 25) {
            alert("Candles are loading, please wait...");
            return;
        }
        mIsReplayMode = true;
        mReplayCandles = [...mFullCandles];
        
        // Start replay 50 bars back or at least before live entry if available
        let startBack = 50;
        if (mActiveLivePosition) {
            let entryTimeSec = mActiveLivePosition.entry_time || 0;
            if (entryTimeSec > 1e11) entryTimeSec = Math.floor(entryTimeSec / 1000);
            const entryIdx = mReplayCandles.findIndex(c => c.time >= entryTimeSec);
            if (entryIdx !== -1) {
                // Start replay 8 bars before trade entry so user can watch setup form and enter!
                startBack = Math.max(15, mReplayCandles.length - Math.max(0, entryIdx - 8));
            }
        }

        mReplayIndex = Math.max(20, mReplayCandles.length - startBack);

        const bar = document.getElementById("mobileReplayBar");
        if (bar) bar.style.display = "flex";
        const btn = document.getElementById("btnMobileReplay");
        if (btn) btn.classList.add("btn-replay-active");

        const scrubber = document.getElementById("mReplayScrubber");
        if (scrubber) {
            scrubber.min = 20;
            scrubber.max = mReplayCandles.length;
            scrubber.value = mReplayIndex;
        }

        updateMobileReplayDisplay();
    }

    function updateMobileReplayDisplay() {
        const visible = mReplayCandles.slice(0, mReplayIndex);
        if (mCandleSeries) mCandleSeries.setData(visible);

        updateChartMarkers();

        if (visible.length > 0) {
            const lastBar = visible[visible.length - 1];
            updateChartHeaderOHLC(lastBar);

            if (mIsHermesStratActive) {
                checkHermes30SetupOnReplay(visible);
            }
            if (mSimTrade && mSimTrade.active) {
                evaluateActiveReplaySimTrade(lastBar);
            }
        }

        const cnt = document.getElementById("mReplayCounterText");
        if (cnt) cnt.innerText = `Bar ${mReplayIndex} / ${mReplayCandles.length}`;
        const scrubber = document.getElementById("mReplayScrubber");
        if (scrubber) scrubber.value = mReplayIndex;
    }

    function toggleMobileReplayPlayPause() {
        const btn = document.getElementById("btnMobileReplayPlay");
        if (mReplayTimer) {
            clearInterval(mReplayTimer);
            mReplayTimer = null;
            if (btn) {
                btn.innerHTML = '<i class="fa-solid fa-play"></i> Play';
                btn.classList.remove('active-play');
            }
        } else {
            if (mReplayIndex >= mReplayCandles.length) {
                mReplayIndex = Math.max(20, mReplayCandles.length - 50);
            }
            if (btn) {
                btn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
                btn.classList.add('active-play');
            }
            mReplayTimer = setInterval(stepMobileReplayForward, mReplaySpeedMs);
        }
    }

    function stepMobileReplayForward() {
        if (mReplayIndex < mReplayCandles.length) {
            const nextCandle = mReplayCandles[mReplayIndex++];
            if (mCandleSeries) mCandleSeries.update(nextCandle);
            updateChartHeaderOHLC(nextCandle);

            updateChartMarkers();

            const cnt = document.getElementById("mReplayCounterText");
            if (cnt) cnt.innerText = `Bar ${mReplayIndex} / ${mReplayCandles.length}`;
            const scrubber = document.getElementById("mReplayScrubber");
            if (scrubber) scrubber.value = mReplayIndex;

            const visible = mReplayCandles.slice(0, mReplayIndex);
            if (mIsHermesStratActive) {
                checkHermes30SetupOnReplay(visible);
            }
            if (mSimTrade && mSimTrade.active) {
                evaluateActiveReplaySimTrade(nextCandle);
            }
        } else {
            toggleMobileReplayPlayPause();
        }
    }

    function stepMobileReplayBackward() {
        if (mReplayIndex > 20) {
            mReplayIndex--;
            updateMobileReplayDisplay();
        }
    }

    function resetMobileReplayToStart() {
        mReplayIndex = Math.max(20, mReplayCandles.length - 50);
        updateMobileReplayDisplay();
    }

    function onMobileReplayScrubberChange(val) {
        mReplayIndex = parseInt(val, 10);
        updateMobileReplayDisplay();
    }

    function setMobileReplaySpeed(spd, btn) {
        document.querySelectorAll(".m-speed-pill").forEach(b => b.classList.remove("active"));
        if (btn) btn.classList.add("active");
        if (spd === 1) mReplaySpeedMs = 800;
        else if (spd === 2) mReplaySpeedMs = 400;
        else if (spd === 5) mReplaySpeedMs = 150;

        if (mReplayTimer) {
            clearInterval(mReplayTimer);
            mReplayTimer = setInterval(stepMobileReplayForward, mReplaySpeedMs);
        }
    }

    function toggleMobileHermesStrategy() {
        mIsHermesStratActive = !mIsHermesStratActive;
        const btn = document.getElementById("btnMobileHermesStrat");
        const txt = document.getElementById("mReplayStratText");
        if (btn) {
            if (mIsHermesStratActive) {
                btn.classList.add("active-strat");
                if (txt) txt.innerText = "Hermes 2A: ON";
            } else {
                btn.classList.remove("active-strat");
                if (txt) txt.innerText = "Hermes 2A: OFF";
                dismissReplaySignal();
            }
        }
    }

    function toggleMobileAutoTrade() {
        mIsAutoTrade = !mIsAutoTrade;
        const btn = document.getElementById("btnMobileAutoTrade");
        const txt = document.getElementById("mReplayAutoText");
        if (btn) {
            if (mIsAutoTrade) {
                btn.classList.add("active-auto");
                if (txt) txt.innerText = "Auto: ON";
            } else {
                btn.classList.remove("active-auto");
                if (txt) txt.innerText = "Auto: OFF";
            }
        }
    }

    function exitMobileReplay() {
        if (mReplayTimer) {
            clearInterval(mReplayTimer);
            mReplayTimer = null;
        }
        mIsReplayMode = false;
        const bar = document.getElementById("mobileReplayBar");
        if (bar) bar.style.display = "none";
        const btn = document.getElementById("btnMobileReplay");
        if (btn) btn.classList.remove("btn-replay-active");
        const playBtn = document.getElementById("btnMobileReplayPlay");
        if (playBtn) {
            playBtn.innerHTML = '<i class="fa-solid fa-play"></i> Play';
            playBtn.classList.remove('active-play');
        }
        dismissReplaySignal();
        clearReplayPriceLines();
        
        if (mCandleSeries && mFullCandles) {
            mCandleSeries.setData(mFullCandles);
            updateChartMarkers();
            renderLivePositionLines();
            if (mFullCandles.length > 0) updateChartHeaderOHLC(mFullCandles[mFullCandles.length - 1]);
        }
    }

    // -------------------------------------------------------------
    // REPLAY SETUP EVALUATION & INTERACTIVE BUY/SELL SIGNAL CARD
    // -------------------------------------------------------------

    function checkHermes30SetupOnReplay(visibleCandles) {
        if (!visibleCandles || visibleCandles.length < 20) return;
        if (mSimTrade && mSimTrade.active) {
            dismissReplaySignal();
            return;
        }

        const n = visibleCandles.length;
        const currentBar = visibleCandles[n - 1];

        // Check if there is a detected setup on this bar or within last 2 bars
        const match = mDetectedSetups.find(s => Math.abs(s.candleIndex - (n - 1)) <= 1);
        if (match) {
            if (!mCurrentSetup || mCurrentSetup.candleTime !== match.candleTime) {
                mCurrentSetup = match;
                showReplaySignalCard(match);
                playInstitutionalChime("signal");

                if (mIsAutoTrade) {
                    executeCurrentReplaySignal();
                }
            }
        } else {
            if (mCurrentSetup && Math.abs((n - 1) - mCurrentSetup.candleIndex) > 3) {
                dismissReplaySignal();
                mCurrentSetup = null;
            }
        }
    }

    function showReplaySignalCard(setup) {
        const card = document.getElementById("mobileReplaySignalCard");
        if (!card) return;

        const isLong = setup.side === "BUY";
        const badge = document.getElementById("mRscBadge");
        if (badge) {
            badge.className = `rsc-badge ${isLong ? 'rsc-badge-long' : 'rsc-badge-short'}`;
            badge.innerHTML = isLong 
                ? '<i class="fa-solid fa-arrow-trend-up"></i> HERMES 3.5 RADAR HARVEST • LONG BUY' 
                : '<i class="fa-solid fa-arrow-trend-down"></i> HERMES 3.5 RADAR HARVEST • SHORT SELL';
        }

        const ep = document.getElementById("mRscEntry");
        if (ep) ep.innerText = `$${setup.entryPrice.toFixed(setup.entryPrice < 1 ? 4 : 2)}`;
        const tp = document.getElementById("mRscTp");
        if (tp) tp.innerText = `$${setup.tpPrice.toFixed(setup.tpPrice < 1 ? 4 : 2)} (+14% ROE)`;
        const sl = document.getElementById("mRscSl");
        if (sl) sl.innerText = `$${setup.hardSlPrice.toFixed(setup.hardSlPrice < 1 ? 4 : 2)} (-14% ROE)`;
        const dw = document.getElementById("mRscDisp");
        if (dw) dw.innerText = `+${setup.displacementPct}% / ${setup.wickRatioPct}% Wick`;

        const btn = document.getElementById("btnMobileExecuteSignal");
        if (btn) {
            btn.innerHTML = `<i class="fa-solid fa-bolt"></i> Execute Simulated ${isLong ? 'LONG BUY' : 'SHORT SELL'} @ 5% Boundary`;
        }

        card.style.display = "block";
    }

    function dismissReplaySignal() {
        const card = document.getElementById("mobileReplaySignalCard");
        if (card) card.style.display = "none";
    }

    // -------------------------------------------------------------
    // SIMULATED TRADE EXECUTION & STEPPED TRAILING SL LADDER
    // -------------------------------------------------------------

    function executeCurrentReplaySignal() {
        if (!mCurrentSetup) return;
        const s = mCurrentSetup;

        mSimTrade = {
            active: true,
            symbol: mSymbol,
            side: s.side,
            entryPrice: s.entryPrice,
            tpPrice: s.tpPrice,
            slPrice: s.hardSlPrice,
            hardSlPrice: s.hardSlPrice,
            softSlPrice: s.softSlPrice,
            peakRoi: 0.0,
            lockedRoi: 0.0,
            currentStep: 0,
            durationBars: 0,
            filled: true,
            fillPrice: s.entryPrice,
            entryTime: s.candleTime
        };

        dismissReplaySignal();
        updateReplayPriceLines();
        renderReplayActiveHUD();
        showOutcomeBanner("⚡ ORDER EXECUTED", `${s.side === 'BUY' ? 'LONG' : 'SHORT'} 5X Filled @ $${s.entryPrice.toFixed(s.entryPrice < 1 ? 4 : 2)} (5% Boundary)`, "info");
        playInstitutionalChime("shield");
    }

    function updateReplayPriceLines() {
        clearReplayPriceLines();
        if (!mCandleSeries || !mSimTrade) return;

        const t = mSimTrade;
        try {
            mPriceLines.entry = mCandleSeries.createPriceLine({
                price: t.entryPrice,
                color: '#00DFC0',
                lineWidth: 2,
                lineStyle: window.LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: '5% BOUNDARY ENTRY'
            });

            mPriceLines.tp = mCandleSeries.createPriceLine({
                price: t.tpPrice,
                color: '#00C087',
                lineWidth: 2,
                lineStyle: window.LightweightCharts.LineStyle.Solid,
                axisLabelVisible: true,
                title: 'TP (+14% ROE)'
            });

            const isTrailing = (t.lockedRoi || 0) > 0;
            mPriceLines.sl = mCandleSeries.createPriceLine({
                price: t.slPrice,
                color: isTrailing ? '#FFB800' : '#FF4B55',
                lineWidth: 2,
                lineStyle: isTrailing ? window.LightweightCharts.LineStyle.Solid : window.LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: isTrailing ? `ARMOR SL (+${t.lockedRoi.toFixed(1)}% ROI)` : 'STOP LOSS (-14% ROE)'
            });
        } catch(e) {}
    }

    function clearReplayPriceLines() {
        if (!mCandleSeries) return;
        try {
            if (mPriceLines.entry) mCandleSeries.removePriceLine(mPriceLines.entry);
            if (mPriceLines.tp) mCandleSeries.removePriceLine(mPriceLines.tp);
            if (mPriceLines.sl) mCandleSeries.removePriceLine(mPriceLines.sl);
        } catch(e) {}
        mPriceLines.entry = null;
        mPriceLines.tp = null;
        mPriceLines.sl = null;
    }

    function evaluateActiveReplaySimTrade(candle) {
        if (!mSimTrade || !mSimTrade.active) return;

        const t = mSimTrade;
        const isLong = t.side === "BUY" || t.side === "LONG";
        const leverage = 5.0;
        t.durationBars = (t.durationBars || 0) + 1;

        const barHigh = candle.high;
        const barLow = candle.low;
        const barClose = candle.close;

        let highRoi = isLong 
            ? ((barHigh - t.entryPrice) / t.entryPrice) * 100 * leverage
            : ((t.entryPrice - barLow) / t.entryPrice) * 100 * leverage;

        if (highRoi > t.peakRoi) {
            t.peakRoi = highRoi;
        }

        const currRoe = isLong
            ? ((barClose - t.entryPrice) / t.entryPrice) * 100 * leverage
            : ((t.entryPrice - barClose) / t.entryPrice) * 100 * leverage;
        t.currRoe = currRoe;

        // Stepped Trailing Profit Armor Ladder (+5% -> +1%, +9.5% -> +5%, +14.5% -> +10%)
        let targetLocked = t.lockedRoi || 0;
        let targetStep = t.currentStep || 0;

        if (t.peakRoi >= 5.0 && targetLocked < 1.0) { targetLocked = 1.0; targetStep = 1; }
        if (t.peakRoi >= 9.5 && targetLocked < 5.0) { targetLocked = 5.0; targetStep = 2; }
        if (t.peakRoi >= 14.5 && targetLocked < 10.0) { targetLocked = 10.0; targetStep = 3; }
        if (t.peakRoi >= 19.5 && targetLocked < 15.0) { targetLocked = 15.0; targetStep = 4; }
        if (t.peakRoi >= 24.5 && targetLocked < 20.0) { targetLocked = 20.0; targetStep = 5; }

        if (targetLocked > (t.lockedRoi || 0)) {
            t.lockedRoi = targetLocked;
            t.currentStep = targetStep;
            const spotShift = (targetLocked / 100.0) / leverage;
            t.slPrice = isLong ? t.entryPrice * (1.0 + spotShift) : t.entryPrice * (1.0 - spotShift);
            updateReplayPriceLines();
            renderReplayActiveHUD();
            showOutcomeBanner(`🛡️ PROFIT ARMOR STEP ${targetStep}`, `SL Raised to +${targetLocked.toFixed(1)}% ROI Protected`, "shield");
            playInstitutionalChime("shield");
        }

        // Take Profit Check (+14.0% ROE)
        const tpHit = isLong ? (barHigh >= t.tpPrice) : (barLow <= t.tpPrice);
        if (tpHit) {
            resolveReplayTrade("TAKE_PROFIT", t.tpPrice, +14.0, candle);
            return;
        }

        // Trailing SL Check
        if (t.lockedRoi > 0) {
            const trailingHit = isLong ? (barLow <= t.slPrice) : (barHigh >= t.slPrice);
            if (trailingHit) {
                resolveReplayTrade("TRAILING_SL", t.slPrice, t.lockedRoi, candle);
                return;
            }
        }

        // Hard SL Check (-14.0% ROE)
        const slHit = isLong ? (barLow <= t.hardSlPrice) : (barHigh >= t.hardSlPrice);
        if (slHit) {
            resolveReplayTrade("STOP_LOSS", t.hardSlPrice, -14.0, candle);
            return;
        }

        renderReplayActiveHUD();
    }

    function renderReplayActiveHUD() {
        const hud = document.getElementById("mobileReplayActiveHUD");
        if (!hud || !mSimTrade) return;

        const t = mSimTrade;
        const isLong = t.side === "BUY" || t.side === "LONG";

        const b = document.getElementById("mRahSide");
        if (b) {
            b.className = `rah-badge ${isLong ? 'rah-long' : 'rah-short'}`;
            b.innerText = `${isLong ? 'LONG' : 'SHORT'} 5X (SIM)`;
        }

        const ep = document.getElementById("mRahEntry");
        if (ep) ep.innerText = `$${t.entryPrice.toFixed(t.entryPrice < 1 ? 4 : 2)}`;

        const curP = mReplayCandles && mReplayIndex > 0 ? mReplayCandles[mReplayIndex - 1].close : t.entryPrice;
        const cur = document.getElementById("mRahCur");
        if (cur) cur.innerText = `$${curP.toFixed(curP < 1 ? 4 : 2)}`;

        const roeEl = document.getElementById("mRahRoe");
        if (roeEl) {
            const roe = t.currRoe || 0.0;
            roeEl.className = roe >= 0 ? "val-green" : "val-red";
            roeEl.innerText = `${roe >= 0 ? '+' : ''}${roe.toFixed(2)}%`;
        }

        const pkEl = document.getElementById("mRahPeak");
        if (pkEl) pkEl.innerText = `+${(t.peakRoi || 0).toFixed(1)}%`;

        const armEl = document.getElementById("mRahArmor");
        if (armEl) {
            if (t.currentStep > 0) {
                armEl.innerHTML = `<span style="color:var(--gold); font-weight:800;">Step ${t.currentStep}: +${t.lockedRoi.toFixed(1)}% Locked</span>`;
            } else {
                armEl.innerText = "Initial Shield (-14% ROE)";
            }
        }

        hud.style.display = "block";
    }

    function closeReplayTradeManual() {
        if (!mSimTrade) return;
        const curP = mReplayCandles && mReplayIndex > 0 ? mReplayCandles[mReplayIndex - 1].close : mSimTrade.entryPrice;
        const curC = mReplayCandles && mReplayIndex > 0 ? mReplayCandles[mReplayIndex - 1] : { time: Math.floor(Date.now() / 1000) };
        resolveReplayTrade("MANUAL_EXIT", curP, mSimTrade.currRoe || 0.0, curC);
    }

    function resolveReplayTrade(outcome, exitPrice, roePct, candle) {
        if (!mSimTrade) return;
        const t = mSimTrade;
        const pnlUsdt = 50.0 * (roePct / 100.0);

        const record = {
            id: mSimJournal.length + 1,
            symbol: mSymbol,
            side: t.side === "BUY" ? "LONG" : "SHORT",
            entryPrice: t.entryPrice,
            exitPrice: exitPrice,
            outcome: outcome,
            roePct: roePct,
            pnlUsdt: pnlUsdt,
            lockedRoi: t.lockedRoi || 0,
            durationBars: t.durationBars || 1,
            exitTime: candle.time
        };

        mSimJournal.unshift(record);
        updateReplayJournalBadge();

        if (outcome === "TAKE_PROFIT") {
            showOutcomeBanner("🏆 TAKE PROFIT HIT!", `+${roePct.toFixed(2)}% ROE (+$${pnlUsdt.toFixed(2)}) Target Hit!`, "win");
            playInstitutionalChime("win");
        } else if (outcome === "TRAILING_SL") {
            showOutcomeBanner("🛡️ TRAILING SL SECURED!", `+${roePct.toFixed(2)}% ROE Profit Protected (+$${pnlUsdt.toFixed(2)})`, "win");
            playInstitutionalChime("shield");
        } else if (outcome === "STOP_LOSS") {
            showOutcomeBanner("🛑 STOP LOSS HIT", `${roePct.toFixed(2)}% ROE (-$${Math.abs(pnlUsdt).toFixed(2)}) Defense Triggered`, "loss");
        } else {
            showOutcomeBanner("⚡ MANUAL EXIT", `${roePct >= 0 ? '+' : ''}${roePct.toFixed(2)}% ROE ($${pnlUsdt.toFixed(2)})`, "info");
        }

        mSimTrade = null;
        clearReplayPriceLines();
        const hud = document.getElementById("mobileReplayActiveHUD");
        if (hud) hud.style.display = "none";
    }

    function showOutcomeBanner(title, subtitle, type = "win") {
        const banner = document.getElementById("mobileReplayBanner");
        if (!banner) return;

        banner.className = `replay-outcome-banner ${type}`;
        const t = document.getElementById("mRobTitle");
        if (t) t.innerText = title;
        const s = document.getElementById("mRobSubtitle");
        if (s) s.innerText = subtitle;

        const ic = document.getElementById("mRobIcon");
        if (ic) {
            if (type === "win") ic.innerHTML = '<i class="fa-solid fa-trophy"></i>';
            else if (type === "shield") ic.innerHTML = '<i class="fa-solid fa-shield-halved"></i>';
            else if (type === "loss") ic.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
            else ic.innerHTML = '<i class="fa-solid fa-bolt"></i>';
        }

        banner.style.display = "flex";
        if (mBannerTimeout) clearTimeout(mBannerTimeout);
        mBannerTimeout = setTimeout(() => { banner.style.display = "none"; }, 2800);
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

    // -------------------------------------------------------------
    // REPLAY BACKTEST JOURNAL
    // -------------------------------------------------------------

    function updateReplayJournalBadge() {
        const el = document.getElementById("mobileJournalBadgeCount");
        if (el) el.innerText = mSimJournal.length;
    }

    function openReplayJournalModal() {
        renderReplayJournalTable();
        const m = document.getElementById("mobileJournalModal");
        if (m) m.style.display = "flex";
    }

    function closeReplayJournalModal() {
        const m = document.getElementById("mobileJournalModal");
        if (m) m.style.display = "none";
    }

    function clearReplayJournal() {
        if (confirm("Reset Replay Backtest Journal?")) {
            mSimJournal = [];
            updateReplayJournalBadge();
            renderReplayJournalTable();
        }
    }

    function renderReplayJournalTable() {
        const total = mSimJournal.length;
        const wins = mSimJournal.filter(x => x.roePct > 0).length;
        const losses = mSimJournal.filter(x => x.roePct < 0).length;
        const winRate = total > 0 ? ((wins / total) * 100).toFixed(1) : "0.0";
        const netReturn = mSimJournal.reduce((acc, x) => acc + x.roePct, 0);

        const totEl = document.getElementById("mRjmTotal");
        if (totEl) totEl.innerText = total;
        const wrEl = document.getElementById("mRjmWinRate");
        if (wrEl) wrEl.innerText = `${winRate}%`;
        const wEl = document.getElementById("mRjmWins");
        if (wEl) wEl.innerText = wins;
        const lEl = document.getElementById("mRjmLosses");
        if (lEl) lEl.innerText = losses;
        const netEl = document.getElementById("mRjmNet");
        if (netEl) {
            netEl.className = `rjm-stat-val ${netReturn >= 0 ? 'val-green' : 'val-red'}`;
            netEl.innerText = `${netReturn >= 0 ? '+' : ''}${netReturn.toFixed(2)}%`;
        }

        const tbody = document.getElementById("mRjmTableBody");
        if (!tbody) return;

        if (mSimJournal.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding:20px;">No simulated trades yet. Run Bar Replay to trigger Hermes 3.5 setups!</td></tr>';
            return;
        }

        tbody.innerHTML = mSimJournal.map((t, idx) => {
            const isWin = t.roePct > 0;
            const outcomeBadge = t.outcome === "TAKE_PROFIT" 
                ? '<span style="color:var(--buy-green); font-weight:800;">🏆 TP (+14%)</span>'
                : (t.outcome === "TRAILING_SL" 
                    ? `<span style="color:var(--gold); font-weight:800;">🛡️ TRAIL (+${t.lockedRoi}%)</span>`
                    : (t.outcome === "STOP_LOSS" 
                        ? '<span style="color:var(--sell-red); font-weight:800;">🛑 SL (-14%)</span>' 
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
                    <td style="color:var(--text-muted);">${t.durationBars}b</td>
                </tr>
            `;
        }).join("");
    }

    // -------------------------------------------------------------
    // ROBUST LANDSCAPE & FULLSCREEN ROTATION CONTROLLER
    // -------------------------------------------------------------

    let mIsFullscreen = false;

    async function toggleMobileFullscreen() {
        const chartWrapper = document.getElementById("mobileChartSectionWrapper");
        if (!chartWrapper || !mChart) return;

        mIsFullscreen = !mIsFullscreen;

        if (mIsFullscreen) {
            chartWrapper.classList.add("chart-fullscreen-active");
            document.body.classList.add("chart-fs-open");

            updateFullscreenButtonLabels(true);

            // Request native browser fullscreen if supported
            try {
                if (chartWrapper.requestFullscreen) {
                    await chartWrapper.requestFullscreen();
                } else if (chartWrapper.webkitRequestFullscreen) {
                    await chartWrapper.webkitRequestFullscreen();
                }
            } catch(e) {}

            setTimeout(resizeFullscreenChart, 50);
            setTimeout(resizeFullscreenChart, 180);
        } else {
            chartWrapper.classList.remove("chart-fullscreen-active");
            document.body.classList.remove("chart-fs-open");

            updateFullscreenButtonLabels(false);

            try {
                if (document.exitFullscreen) {
                    await document.exitFullscreen();
                } else if (document.webkitExitFullscreen) {
                    await document.webkitExitFullscreen();
                }
            } catch(e) {}

            setTimeout(() => {
                const w = chartWrapper.clientWidth || 360;
                if (mChart) {
                    mChart.applyOptions({ width: w, height: 480 });
                    mChart.timeScale().applyOptions({ rightOffset: 18 });
                    mChart.timeScale().fitContent();
                    drawMobileHermes35Boxes();
                }
            }, 80);
        }
    }

    function updateFullscreenButtonLabels(isFs) {
        const btnHero = document.getElementById("btnMobileFullscreen") || document.getElementById("btnMobileLandscape");
        const btnHeader = document.getElementById("btnTvHeaderFullscreen");
        const fsText = document.getElementById("mTvFsBtnText");

        if (isFs) {
            if (btnHero) btnHero.innerHTML = '<i class="fa-solid fa-compress"></i> Exit';
            if (btnHeader) {
                btnHeader.innerHTML = '<i class="fa-solid fa-compress" style="color:#FFF;"></i> <span id="mTvFsBtnText">Exit Fullscreen</span>';
                btnHeader.style.background = '#EF4444';
                btnHeader.style.borderColor = '#DC2626';
                btnHeader.style.color = '#FFFFFF';
            }
        } else {
            if (btnHero) btnHero.innerHTML = '<i class="fa-solid fa-expand"></i> Fullscreen';
            if (btnHeader) {
                btnHeader.innerHTML = '<i class="fa-solid fa-expand" style="color:var(--brand-teal);"></i> <span id="mTvFsBtnText">Fullscreen</span>';
                btnHeader.style.background = 'rgba(0,223,192,0.15)';
                btnHeader.style.borderColor = 'var(--brand-teal)';
                btnHeader.style.color = 'var(--brand-teal)';
            }
        }
    }

    function resizeFullscreenChart() {
        if (!mIsFullscreen || !mChart) return;
        const chartWrapper = document.getElementById("mobileChartSectionWrapper");
        if (!chartWrapper) return;

        const w = window.innerWidth || document.documentElement.clientWidth || screen.width;
        const h = window.innerHeight || document.documentElement.clientHeight || screen.height;

        const tvBar = document.getElementById("mChartTvHeaderStrip");
        const ctrlBar = chartWrapper.querySelector(".chart-controls-wrapper");
        const ohlcBar = chartWrapper.querySelector(".chart-ohlc-bar");
        const replayBar = document.getElementById("mobileReplayBar");

        let headerOffset = (tvBar ? tvBar.offsetHeight : 34) 
                         + (ctrlBar ? ctrlBar.offsetHeight : 38)
                         + (ohlcBar ? ohlcBar.offsetHeight : 22);

        if (replayBar && replayBar.style.display !== "none") {
            headerOffset += replayBar.offsetHeight;
        }

        const chartH = Math.max(260, h - headerOffset);
        mChart.applyOptions({ width: w, height: chartH });
        mChart.timeScale().applyOptions({ rightOffset: 18 });
        mChart.timeScale().fitContent();
        drawMobileHermes35Boxes();
    }

    // Auto-sync fullscreen changes (hardware back button or browser gesture)
    document.addEventListener("fullscreenchange", () => {
        if (!document.fullscreenElement && mIsFullscreen) {
            toggleMobileFullscreen();
        }
    });
    document.addEventListener("webkitfullscreenchange", () => {
        if (!document.webkitFullscreenElement && mIsFullscreen) {
            toggleMobileFullscreen();
        }
    });
    window.addEventListener("resize", () => {
        if (mIsFullscreen) {
            resizeFullscreenChart();
        } else if (mChart) {
            const chartWrapper = document.getElementById("mobileChartSectionWrapper");
            if (chartWrapper) {
                mChart.applyOptions({ width: chartWrapper.clientWidth || 360, height: 480 });
                mChart.timeScale().fitContent();
            }
        }
    });
    window.addEventListener("orientationchange", () => {
        setTimeout(() => {
            if (mIsFullscreen) resizeFullscreenChart();
            else if (mChart) {
                const chartWrapper = document.getElementById("mobileChartSectionWrapper");
                if (chartWrapper) {
                    mChart.applyOptions({ width: chartWrapper.clientWidth || 360, height: 480 });
                    mChart.timeScale().fitContent();
                }
            }
        }, 150);
    });

    // -------------------------------------------------------------
    // CUSTOMIZABLE DRAG RULER MEASURE TOOL (ENLARGED TOUCH HANDLES)
    // -------------------------------------------------------------

    function initMeasureToolOverlay() {
        const overlay = document.getElementById("mobileMeasureOverlay");
        if (!overlay) return;

        overlay.addEventListener("pointerdown", onMeasureDown);
        overlay.addEventListener("pointermove", onMeasureMove);
        overlay.addEventListener("pointerup", onMeasureUp);
        overlay.addEventListener("pointercancel", onMeasureUp);

        const h1 = document.getElementById("mMeasureHandle1");
        const h2 = document.getElementById("mMeasureHandle2");

        if (h1) {
            h1.addEventListener("pointerdown", e => {
                e.stopPropagation();
                e.preventDefault();
                mDraggingHandle = 1;
                try { h1.setPointerCapture(e.pointerId); } catch(err) {}
            });
            h1.addEventListener("pointermove", onHandleMove);
            h1.addEventListener("pointerup", onHandleUp);
            h1.addEventListener("pointercancel", onHandleUp);
        }

        if (h2) {
            h2.addEventListener("pointerdown", e => {
                e.stopPropagation();
                e.preventDefault();
                mDraggingHandle = 2;
                try { h2.setPointerCapture(e.pointerId); } catch(err) {}
            });
            h2.addEventListener("pointermove", onHandleMove);
            h2.addEventListener("pointerup", onHandleUp);
            h2.addEventListener("pointercancel", onHandleUp);
        }
    }

    function toggleMobileMeasureTool() {
        const overlay = document.getElementById("mobileMeasureOverlay");
        const btn = document.getElementById("btnMobileMeasure");
        if (!overlay) return;

        if (mIsMeasureActive) {
            clearMobileMeasureTool();
        } else {
            mIsMeasureActive = true;
            mIsMeasuring = false;
            overlay.style.display = "block";
            overlay.classList.add("drawing-mode");
            if (btn) btn.classList.add("btn-measure-active");
        }
    }

    function clearMobileMeasureTool() {
        mIsMeasureActive = false;
        mIsMeasuring = false;
        mDraggingHandle = null;
        mMeasurePt1 = null;
        mMeasurePt2 = null;

        const overlay = document.getElementById("mobileMeasureOverlay");
        if (overlay) {
            overlay.classList.remove("drawing-mode");
            overlay.style.display = "none";
        }
        const btn = document.getElementById("btnMobileMeasure");
        if (btn) btn.classList.remove("btn-measure-active");

        const badge = document.getElementById("mMeasureBadge");
        if (badge) badge.style.display = "none";
        const ab = document.getElementById("mMeasureActionBar");
        if (ab) ab.style.display = "none";

        const box = document.getElementById("mMeasureBox");
        if (box) { box.setAttribute("width", "0"); box.setAttribute("height", "0"); }
        const topL = document.getElementById("mMeasureLineTop");
        if (topL) { topL.setAttribute("x1", "0"); topL.setAttribute("x2", "0"); }
        const btmL = document.getElementById("mMeasureLineBottom");
        if (btmL) { btmL.setAttribute("x1", "0"); btmL.setAttribute("x2", "0"); }
        const ctrL = document.getElementById("mMeasureLineCenter");
        if (ctrL) { ctrL.setAttribute("x1", "0"); ctrL.setAttribute("x2", "0"); }
        const h1 = document.getElementById("mMeasureHandle1");
        if (h1) { h1.setAttribute("cx", "-999"); h1.setAttribute("cy", "-999"); }
        const h2 = document.getElementById("mMeasureHandle2");
        if (h2) { h2.setAttribute("cx", "-999"); h2.setAttribute("cy", "-999"); }
    }

    function getCoordsFromPointer(e) {
        const container = document.getElementById("mobileChartCanvas");
        if (!container || !mChart || !mCandleSeries) return null;
        const rect = container.getBoundingClientRect();
        const x = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
        const y = Math.max(0, Math.min(rect.height, e.clientY - rect.top));

        let price = null;
        try { price = mCandleSeries.coordinateToPrice(y); } catch(err) {}
        if (price === null && mFullCandles && mFullCandles.length > 0) {
            price = mFullCandles[mFullCandles.length - 1].close;
        }

        return { x, y, price };
    }

    function onMeasureDown(e) {
        if (!mIsMeasureActive) return;
        e.preventDefault();
        e.stopPropagation();

        const pt = getCoordsFromPointer(e);
        if (!pt || pt.price === null) return;

        if (!mIsMeasuring) {
            mIsMeasuring = true;
            mMeasurePt1 = pt;
            mMeasurePt2 = pt;
            renderMeasureShape();
        } else {
            mIsMeasuring = false;
            mMeasurePt2 = pt;
            renderMeasureShape();
            const overlay = document.getElementById("mobileMeasureOverlay");
            if (overlay) overlay.classList.remove("drawing-mode");
        }
    }

    function onMeasureMove(e) {
        if (!mIsMeasureActive || !mIsMeasuring || !mMeasurePt1) return;
        const pt = getCoordsFromPointer(e);
        if (!pt || pt.price === null) return;
        mMeasurePt2 = pt;
        renderMeasureShape();
    }

    function onMeasureUp() {
        if (mIsMeasuring && mMeasurePt1 && mMeasurePt2) {
            const dx = Math.abs(mMeasurePt2.x - mMeasurePt1.x);
            const dy = Math.abs(mMeasurePt2.y - mMeasurePt1.y);
            if (dx > 10 || dy > 10) {
                mIsMeasuring = false;
                const overlay = document.getElementById("mobileMeasureOverlay");
                if (overlay) overlay.classList.remove("drawing-mode");
            }
        }
    }

    function onHandleMove(e) {
        if (!mDraggingHandle) return;
        e.preventDefault();
        e.stopPropagation();
        const pt = getCoordsFromPointer(e);
        if (!pt || pt.price === null) return;

        if (mDraggingHandle === 1) mMeasurePt1 = pt;
        else if (mDraggingHandle === 2) mMeasurePt2 = pt;
        renderMeasureShape();
    }

    function onHandleUp(e) {
        if (!mDraggingHandle) return;
        try {
            if (e.target && e.target.releasePointerCapture) {
                e.target.releasePointerCapture(e.pointerId);
            }
        } catch(err) {}
        mDraggingHandle = null;
    }

    function renderMeasureShape() {
        if (!mMeasurePt1 || !mMeasurePt2) return;

        const x1 = Math.min(mMeasurePt1.x, mMeasurePt2.x);
        const x2 = Math.max(mMeasurePt1.x, mMeasurePt2.x);
        const y1 = Math.min(mMeasurePt1.y, mMeasurePt2.y);
        const y2 = Math.max(mMeasurePt1.y, mMeasurePt2.y);
        const w = Math.max(2, x2 - x1);
        const h = Math.max(2, y2 - y1);

        const isUp = (mMeasurePt2.price >= mMeasurePt1.price);
        const themeColor = isUp ? '#00C087' : '#FF4B55';
        const fillColor = isUp ? 'rgba(0, 192, 135, 0.14)' : 'rgba(255, 75, 85, 0.14)';

        const box = document.getElementById("mMeasureBox");
        if (box) {
            box.setAttribute("x", x1);
            box.setAttribute("y", y1);
            box.setAttribute("width", w);
            box.setAttribute("height", h);
            box.setAttribute("fill", fillColor);
            box.setAttribute("stroke", themeColor);
        }

        const topL = document.getElementById("mMeasureLineTop");
        if (topL) {
            topL.setAttribute("x1", x1); topL.setAttribute("x2", x2);
            topL.setAttribute("y1", y1); topL.setAttribute("y2", y1);
            topL.setAttribute("stroke", themeColor);
        }

        const btmL = document.getElementById("mMeasureLineBottom");
        if (btmL) {
            btmL.setAttribute("x1", x1); btmL.setAttribute("x2", x2);
            btmL.setAttribute("y1", y2); btmL.setAttribute("y2", y2);
            btmL.setAttribute("stroke", themeColor);
        }

        const ctrL = document.getElementById("mMeasureLineCenter");
        if (ctrL) {
            const cx = x1 + w / 2;
            ctrL.setAttribute("x1", cx); ctrL.setAttribute("x2", cx);
            ctrL.setAttribute("y1", mMeasurePt1.y); ctrL.setAttribute("y2", mMeasurePt2.y);
            ctrL.setAttribute("stroke", themeColor);
        }

        const h1 = document.getElementById("mMeasureHandle1");
        if (h1) {
            h1.setAttribute("cx", mMeasurePt1.x);
            h1.setAttribute("cy", mMeasurePt1.y);
            h1.setAttribute("stroke", themeColor);
        }

        const h2 = document.getElementById("mMeasureHandle2");
        if (h2) {
            h2.setAttribute("cx", mMeasurePt2.x);
            h2.setAttribute("cy", mMeasurePt2.y);
            h2.setAttribute("stroke", themeColor);
        }

        const priceDiff = mMeasurePt2.price - mMeasurePt1.price;
        const pctDiff = mMeasurePt1.price > 0 ? (priceDiff / mMeasurePt1.price) * 100 : 0;
        const sign = priceDiff >= 0 ? "+" : "";

        const badge = document.getElementById("mMeasureBadge");
        const bText = document.getElementById("mMeasureBadgeText");
        if (badge && bText) {
            bText.innerText = `${sign}${priceDiff.toFixed(priceDiff < 1 ? 4 : 2)} (${sign}${pctDiff.toFixed(2)}%)`;
            badge.style.display = "block";
            badge.style.left = `${x1 + w / 2}px`;
            badge.style.top = `${Math.max(10, y1 - 28)}px`;
            badge.style.borderColor = themeColor;
        }

        const ab = document.getElementById("mMeasureActionBar");
        if (ab) {
            ab.style.display = "flex";
            ab.style.left = `${x1 + w / 2}px`;
            ab.style.top = `${y2 + 8}px`;
        }
    }

    // Export to global window namespace
    window.HermesMobileChart = {
        init: initHermesChart,
        setTimeframe: setMobileTimeframe,
        setSymbol: setMobileSymbol,
        toggleFullscreen: toggleMobileFullscreen,
        toggleLandscape: toggleMobileFullscreen,
        toggleReplay: toggleMobileReplay,
        stepForward: stepMobileReplayForward,
        stepBackward: stepMobileReplayBackward,
        togglePlay: toggleMobileReplayPlayPause,
        resetStart: resetMobileReplayToStart,
        setSpeed: setMobileReplaySpeed,
        onScrubberChange: onMobileReplayScrubberChange,
        exitReplay: exitMobileReplay,
        toggleStrategy: toggleMobileHermesStrategy,
        toggleAutoTrade: toggleMobileAutoTrade,
        executeSignal: executeCurrentReplaySignal,
        dismissSignal: dismissReplaySignal,
        closeTrade: closeReplayTradeManual,
        openJournal: openReplayJournalModal,
        closeJournal: closeReplayJournalModal,
        clearJournal: clearReplayJournal,
        toggleMeasure: toggleMobileMeasureTool,
        clearMeasure: clearMobileMeasureTool
    };

})(window);
