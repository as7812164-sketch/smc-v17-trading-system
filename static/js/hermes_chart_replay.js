/**
 * HERMES 3.0 MODEL 2A INTERACTIVE BAR REPLAY & STRATEGY BACKTESTER SUITE
 * =====================================================================
 * Designed specifically for Hermes APEX APK & Mobile Web Terminal.
 * 
 * Features:
 * 1. High-Performance TradingView Lightweight Candlestick Chart with EMAs & Volume.
 * 2. Free Historical Bar Replay Simulator (Start, Step Forward/Backward, Play/Pause, Speed 1x-5x, Scrubber).
 * 3. Real-Time Hermes 3.0 Model 2A Detection Engine:
 *    - Adaptive Displacement (1.5% - 4.0%)
 *    - Decisional Order Block (Fib 0.30 - 0.70) + FVG Imbalance
 *    - Inducement (IDM) Sweep
 *    - 50% Mean Threshold (MT) Tap with Rejection Wick >= 18%
 * 4. Interactive BUY / SELL Signal Card with 50% MT Entry, TP (+14% ROE / 1:2 R:R), SL (-14% ROE).
 * 5. Interactive Simulated Trade Execution & Live Tracking:
 *    - Visual Entry, TP, and dynamic Trailing SL price lines on chart.
 *    - Stepped Trailing Profit Armor (+5% ROI -> +1% Fee Shield, +9.5% -> +5%, +14.5% -> +10%).
 *    - Floating Active Position HUD with Live ROE %, Peak ROI %, and Market Close button.
 *    - Victory / Trailing Shield / SL Hit outcome banners with Web Audio API chimes.
 * 6. Replay Backtest Journal with Win Rate %, Net Return %, P&L, and full Trade Log.
 * 7. Customizable TradingView Price Range / Ruler Measure Tool with enlarged touch handles.
 */

(function(window) {
    'use strict';

    let mChart = null;
    let mCandleSeries = null;
    let mVolumeSeries = null;
    let mEma20Series = null;
    let mEma50Series = null;
    let mEma200Series = null;

    let mSymbol = "BTCUSDT";
    let mInterval = "15m";
    let mFullCandles = [];
    let mIndicatorsState = { ema: true, vol: true, smc: true };

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
    let mPriceLines = { entry: null, tp: null, sl: null };
    let mBannerTimeout = null;

    // Measure Tool State
    let mIsMeasureActive = false;
    let mIsMeasuring = false;
    let mDraggingHandle = null;
    let mMeasurePt1 = null;
    let mMeasurePt2 = null;

    function initHermesChart(containerId = "mobileChartCanvas", defaultSymbol = "BTCUSDT") {
        mSymbol = defaultSymbol.toUpperCase();
        const container = document.getElementById(containerId);
        if (!container || !window.LightweightCharts) return;

        if (mChart) {
            try { mChart.remove(); } catch(e) {}
            mChart = null;
        }

        container.innerHTML = "";

        mChart = window.LightweightCharts.createChart(container, {
            width: container.clientWidth || 360,
            height: container.clientHeight || 340,
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
                vertLine: { color: '#38BDF8', width: 1, style: 2 },
                horzLine: { color: '#38BDF8', width: 1, style: 2 }
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.08)',
                autoScale: true,
                scaleMargins: { top: 0.1, bottom: 0.2 }
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.08)',
                timeVisible: true,
                secondsVisible: false
            }
        });

        // Candlestick Series
        mCandleSeries = mChart.addCandlestickSeries({
            upColor: '#00C087',
            downColor: '#FF4B55',
            borderUpColor: '#00C087',
            borderDownColor: '#FF4B55',
            wickUpColor: '#00C087',
            wickDownColor: '#FF4B55'
        });

        // Volume Series
        mVolumeSeries = mChart.addHistogramSeries({
            color: 'rgba(0, 192, 135, 0.35)',
            priceFormat: { type: 'volume' },
            priceScaleId: '',
            scaleMargins: { top: 0.82, bottom: 0 }
        });

        // EMA Ribbon
        mEma20Series = mChart.addLineSeries({ color: '#FFB800', lineWidth: 1.5, title: 'EMA 20' });
        mEma50Series = mChart.addLineSeries({ color: '#00DFC0', lineWidth: 1.5, title: 'EMA 50' });
        mEma200Series = mChart.addLineSeries({ color: '#A78BFA', lineWidth: 1.5, title: 'EMA 200' });

        // Crosshair move handler
        mChart.subscribeCrosshairMove(param => {
            if (!param || !param.time || !param.seriesPrices) return;
            const bar = param.seriesPrices.get(mCandleSeries);
            if (bar) updateChartHeaderOHLC(bar);
        });

        // Responsive resize
        const ro = new ResizeObserver(entries => {
            if (!entries || !entries.length || !mChart) return;
            const { width, height } = entries[0].contentRect;
            mChart.applyOptions({ width: Math.max(width, 300), height: Math.max(height, 280) });
        });
        ro.observe(container);

        initMeasureToolOverlay();
        loadKlinesData();
    }

    async function loadKlinesData() {
        if (!mCandleSeries) return;
        try {
            const res = await fetch(`/api/klines/${mSymbol}?interval=${mInterval}&limit=160&t=${Date.now()}`);
            if (!res.ok) return;
            const data = await res.json();
            if (!data || !data.candles || !data.candles.length) return;

            mFullCandles = data.candles;
            renderChartIndicators(mFullCandles);

            if (mFullCandles.length > 0) {
                updateChartHeaderOHLC(mFullCandles[mFullCandles.length - 1]);
            }

            mChart.timeScale().fitContent();

            // Update UI label
            const symEl = document.getElementById("mobileChartSymbolText");
            if (symEl) symEl.innerText = mSymbol;
            const priceEl = document.getElementById("mobileChartPriceText");
            if (priceEl && mFullCandles.length > 0) {
                const last = mFullCandles[mFullCandles.length - 1];
                priceEl.innerText = `$${last.close.toFixed(last.close < 1 ? 4 : 2)}`;
            }
        } catch(e) {
            console.warn("Mobile klines load error:", e);
        }
    }

    function renderChartIndicators(candles) {
        if (!mCandleSeries || !candles || !candles.length) return;

        mCandleSeries.setData(candles);

        if (mVolumeSeries && mIndicatorsState.vol) {
            mVolumeSeries.setData(candles.map(c => ({
                time: c.time,
                value: c.volume || 0,
                color: c.close >= c.open ? 'rgba(0, 192, 135, 0.45)' : 'rgba(255, 75, 85, 0.45)'
            })));
        } else if (mVolumeSeries) {
            mVolumeSeries.setData([]);
        }

        if (mIndicatorsState.ema) {
            if (mEma20Series) mEma20Series.setData(calculateEMA(candles, 20));
            if (mEma50Series) mEma50Series.setData(calculateEMA(candles, 50));
            if (mEma200Series) mEma200Series.setData(calculateEMA(candles, 200));
        } else {
            if (mEma20Series) mEma20Series.setData([]);
            if (mEma50Series) mEma50Series.setData([]);
            if (mEma200Series) mEma200Series.setData([]);
        }
    }

    function calculateEMA(candles, period) {
        const k = 2 / (period + 1);
        const result = [];
        let ema = 0;
        for (let i = 0; i < candles.length; i++) {
            const close = candles[i].close;
            if (i < period - 1) {
                ema += close;
            } else if (i === period - 1) {
                ema = (ema + close) / period;
                result.push({ time: candles[i].time, value: ema });
            } else {
                ema = close * k + ema * (1 - k);
                result.push({ time: candles[i].time, value: ema });
            }
        }
        return result;
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
        const dec = c < 1 ? 4 : 2;

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
        if (mIsReplayMode) exitMobileReplay();
        loadKlinesData();
    }

    function setMobileSymbol(sym) {
        mSymbol = sym.toUpperCase();
        if (mIsReplayMode) exitMobileReplay();
        loadKlinesData();
    }

    // ----------------- FREE BAR REPLAY SIMULATOR -----------------

    function toggleMobileReplay() {
        if (mIsReplayMode) {
            exitMobileReplay();
        } else {
            startMobileReplay();
        }
    }

    function startMobileReplay() {
        if (!mFullCandles || mFullCandles.length < 30) {
            alert("Candles are loading, please wait...");
            return;
        }
        mIsReplayMode = true;
        mReplayCandles = [...mFullCandles];
        mReplayIndex = Math.max(25, mReplayCandles.length - 45); // Start 45 bars back

        const bar = document.getElementById("mobileReplayBar");
        if (bar) bar.style.display = "flex";
        const btn = document.getElementById("btnMobileReplay");
        if (btn) btn.classList.add("btn-replay-active");

        const scrubber = document.getElementById("mReplayScrubber");
        if (scrubber) {
            scrubber.min = 25;
            scrubber.max = mReplayCandles.length;
            scrubber.value = mReplayIndex;
        }
        updateMobileReplayDisplay();
    }

    function updateMobileReplayDisplay() {
        const visible = mReplayCandles.slice(0, mReplayIndex);
        renderChartIndicators(visible);

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
                mReplayIndex = Math.max(25, mReplayCandles.length - 45);
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
            if (mVolumeSeries && mIndicatorsState.vol) {
                mVolumeSeries.update({
                    time: nextCandle.time,
                    value: nextCandle.volume || 0,
                    color: nextCandle.close >= nextCandle.open ? 'rgba(0, 192, 135, 0.45)' : 'rgba(255, 75, 85, 0.45)'
                });
            }
            updateChartHeaderOHLC(nextCandle);

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
        if (mReplayIndex > 25) {
            mReplayIndex--;
            updateMobileReplayDisplay();
        }
    }

    function resetMobileReplayToStart() {
        mReplayIndex = Math.max(25, mReplayCandles.length - 45);
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
        const hud = document.getElementById("mobileReplayActiveHUD");
        if (hud) hud.style.display = "none";

        if (mCandleSeries && mFullCandles) {
            renderChartIndicators(mFullCandles);
            if (mFullCandles.length > 0) updateChartHeaderOHLC(mFullCandles[mFullCandles.length - 1]);
        }
    }

    // ----------------- HERMES 3.0 MODEL 2A ALGORITHMIC ENGINE -----------------

    function checkHermes30SetupOnReplay(candles) {
        if (!candles || candles.length < 25) return;
        if (mSimTrade && mSimTrade.active) {
            dismissReplaySignal();
            return;
        }

        const setup = detectHermes30Setup(candles);
        if (setup) {
            if (!mCurrentSetup || mCurrentSetup.candleIndex !== setup.candleIndex || mCurrentSetup.side !== setup.side) {
                mCurrentSetup = setup;
                showReplaySignalCard(setup);
                playInstitutionalChime("signal");

                if (mIsAutoTrade) {
                    executeCurrentReplaySignal();
                }
            }
        } else {
            if (mCurrentSetup && (candles.length - 1 - mCurrentSetup.candleIndex > 4)) {
                dismissReplaySignal();
                mCurrentSetup = null;
            }
        }
    }

    function detectHermes30Setup(candles) {
        const n = candles.length;
        const curr = candles[n - 1];

        let minDisp = 0.025;
        if (mInterval === '15m') minDisp = 0.015;
        else if (mInterval === '1h') minDisp = 0.022;
        else if (mInterval === '4h' || mInterval === '1d') minDisp = 0.038;

        const lookback = Math.min(35, n - 4);
        const startIdx = Math.max(0, n - lookback);

        // Bullish Long
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
                            return {
                                symbol: mSymbol,
                                side: "BUY",
                                type: "LONG",
                                entryPrice: mt,
                                tpPrice: mt * (1.0 + 0.028), // +14% ROE
                                softSlPrice: mt * (1.0 - 0.015),
                                hardSlPrice: mt * (1.0 - 0.028), // -14% ROE
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

        // Bearish Short
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
                            return {
                                symbol: mSymbol,
                                side: "SELL",
                                type: "SHORT",
                                entryPrice: mt,
                                tpPrice: mt * (1.0 - 0.028), // +14% ROE
                                softSlPrice: mt * (1.0 + 0.015),
                                hardSlPrice: mt * (1.0 + 0.028), // -14% ROE
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
        const card = document.getElementById("mobileReplaySignalCard");
        if (!card) return;

        const isLong = setup.side === "BUY";
        const badge = document.getElementById("mRscBadge");
        if (badge) {
            badge.className = `rsc-badge ${isLong ? 'rsc-badge-long' : 'rsc-badge-short'}`;
            badge.innerHTML = isLong 
                ? '<i class="fa-solid fa-arrow-trend-up"></i> HERMES 3.0 MODEL 2A • LONG' 
                : '<i class="fa-solid fa-arrow-trend-down"></i> HERMES 3.0 MODEL 2A • SHORT';
        }

        const ep = document.getElementById("mRscEntry");
        if (ep) ep.innerText = `$${setup.entryPrice.toFixed(4)}`;
        const tp = document.getElementById("mRscTp");
        if (tp) tp.innerText = `$${setup.tpPrice.toFixed(4)} (+14% ROE)`;
        const sl = document.getElementById("mRscSl");
        if (sl) sl.innerText = `$${setup.hardSlPrice.toFixed(4)} (-14% ROE)`;
        const dw = document.getElementById("mRscDisp");
        if (dw) dw.innerText = `+${setup.displacementPct}% / ${setup.wickRatioPct}% Wick`;

        const btn = document.getElementById("btnMobileExecuteSignal");
        if (btn) {
            btn.innerHTML = `<i class="fa-solid fa-bolt"></i> Execute Simulated ${isLong ? 'LONG' : 'SHORT'} @ 50% MT`;
        }

        card.style.display = "block";
    }

    function dismissReplaySignal() {
        const card = document.getElementById("mobileReplaySignalCard");
        if (card) card.style.display = "none";
    }

    function executeCurrentReplaySignal() {
        if (!mCurrentSetup) return;
        const s = mCurrentSetup;

        mSimTrade = {
            active: true,
            symbol: s.symbol,
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
        showOutcomeBanner("⚡ ORDER EXECUTED", `${s.side === 'BUY' ? 'LONG' : 'SHORT'} 5X Filled @ $${s.entryPrice.toFixed(4)} (50% MT)`, "info");
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
                title: '50% MT ENTRY'
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
        mPriceLines = { entry: null, tp: null, sl: null };
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

        // Stepped Trailing Profit Armor
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

        // Take Profit
        const tpHit = isLong ? (barHigh >= t.tpPrice) : (barLow <= t.tpPrice);
        if (tpHit) {
            resolveReplayTrade("TAKE_PROFIT", t.tpPrice, +14.0, candle);
            return;
        }

        // Trailing SL
        if (t.lockedRoi > 0) {
            const trailingHit = isLong ? (barLow <= t.slPrice) : (barHigh >= t.slPrice);
            if (trailingHit) {
                resolveReplayTrade("TRAILING_SL", t.slPrice, t.lockedRoi, candle);
                return;
            }
        }

        // Hard SL
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
        if (ep) ep.innerText = `$${t.entryPrice.toFixed(4)}`;

        const curP = mReplayCandles && mReplayIndex > 0 ? mReplayCandles[mReplayIndex - 1].close : t.entryPrice;
        const cur = document.getElementById("mRahCur");
        if (cur) cur.innerText = `$${curP.toFixed(4)}`;

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
            showOutcomeBanner("🏆 TAKE PROFIT HIT!", `+${roePct.toFixed(2)}% ROE (+$${pnlUsdt.toFixed(2)}) Target Reached!`, "win");
            playInstitutionalChime("win");
        } else if (outcome === "TRAILING_SL") {
            showOutcomeBanner("🛡️ TRAILING SL EXIT!", `+${roePct.toFixed(2)}% ROE Profit Secured (+$${pnlUsdt.toFixed(2)})`, "win");
            playInstitutionalChime("shield");
        } else if (outcome === "STOP_LOSS") {
            showOutcomeBanner("🛑 STOP LOSS HIT", `${roePct.toFixed(2)}% ROE (-$${Math.abs(pnlUsdt).toFixed(2)}) Guard Triggered`, "loss");
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

    // ----------------- REPLAY BACKTEST JOURNAL -----------------

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
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding:20px;">No simulated trades yet. Run Bar Replay to trigger Hermes 3.0 setups!</td></tr>';
            return;
        }

        tbody.innerHTML = mSimJournal.map((t, idx) => {
            const isWin = t.roePct > 0;
            const outcomeBadge = t.outcome === "TAKE_PROFIT" 
                ? '<span style="color:var(--buy-green); font-weight:800;">🏆 TP HIT (+14%)</span>'
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

    // ----------------- CUSTOMIZABLE DRAG RULER MEASURE TOOL -----------------

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
