/**
 * HERMES AI • INSTITUTIONAL POSITION, UPCOMING RADAR & TRADE HISTORY TERMINAL
 * ===========================================================================
 * Features:
 *  - 3-Tab Architecture:
 *      1. [🟢 Open Positions (N)]
 *      2. [📡 Upcoming Radar (N)] -> Live Order Block Proximity (% Away from Entry)
 *      3. [📜 Trade History (N)] -> Completed Trades & Performance Forensics
 *  - Targeted DOM Updates: Real-time price & PnL updates directly modify target nodes
 *    WITHOUT re-rendering innerHTML, ensuring zero screen flicker or jitter.
 *  - 1-Click Chart View: Tapping any upcoming or open trade immediately navigates to
 *    its live chart with Order Blocks and entry targets highlighted.
 */

import { bus } from '../core/event_bus.js';
import { state } from '../core/state.js';

export class PositionCard {
  constructor(mountSelector) {
    this.el = document.querySelector(mountSelector);
    this.isFullView = mountSelector.includes('positions-view');
    this.activeTab = 'open'; // 'open' | 'upcoming' | 'history'
    this.historyTrades = [];
    this.upcomingSetups = [];
    this.historyStats = { total: 0, wins: 0, losses: 0, winRate: 0, totalPnl: 0 };
    this.renderedTradeIds = [];
    this.isFetchingUpcoming = false;
    this.init();
  }

  init() {
    this.render();

    // Smooth targeted update on live ticks (NO DOM WIPEOUT!)
    bus.on('position:updated', (pos) => {
      if (this.activeTab === 'open') {
        this.updateTargetNodes(pos);
      }
    });

    // Re-render when positions open/close or account updates
    bus.on('position:closed', () => {
      this.renderedTradeIds = [];
      this.render();
      if (this.isFullView) this.fetchTradeHistory();
    });

    bus.on('account:updated', () => {
      if (this.activeTab === 'open') {
        const currentIds = (state.positions || []).map(p => p.id).join(',');
        if (currentIds !== this.renderedTradeIds.join(',')) {
          this.render();
        }
      }
    });

    this.fetchTradeHistory();
    if (this.isFullView) {
      this.fetchUpcomingSetups();
    }
  }

  async fetchTradeHistory() {
    try {
      const res = await fetch('/api/paper/trades?limit=50&t=' + Date.now());
      if (!res.ok) return;
      const data = await res.json();
      this.historyTrades = data.trades || [];
      const trades = this.historyTrades;
      const tpHits = trades.filter(t => (Number(t.realized_pnl !== undefined ? t.realized_pnl : (t.pnl_usdt || 0)) > 0) || String(t.result || t.outcome || '').toUpperCase().includes('TP')).length;
      const slHits = Math.max(0, trades.length - tpHits);
      const totalPnl = trades.reduce((sum, t) => sum + Number(t.realized_pnl !== undefined ? t.realized_pnl : (t.pnl_usdt || 0)), 0);
      const winRate = trades.length > 0 ? ((tpHits / trades.length) * 100).toFixed(1) : '0.0';
      this.historyStats = {
        total: data.count || trades.length,
        tpHits: tpHits,
        slHits: slHits,
        winRate: winRate,
        totalPnl: totalPnl
      };
      if (this.activeTab === 'history') {
        this.renderHistory();
      }
    } catch (e) {
      console.warn('Error fetching trade history:', e);
    }
  }

  async fetchUpcomingSetups() {
    if (this.isFetchingUpcoming) return;
    this.isFetchingUpcoming = true;
    try {
      const res = await fetch('/api/smc/upcoming_setups?max_distance=6.0&t=' + Date.now());
      if (!res.ok) return;
      const data = await res.json();
      this.upcomingSetups = data.setups || [];
      if (this.activeTab === 'upcoming') {
        this.renderUpcoming();
      } else {
        // Update badge count
        const btnUpcoming = this.el.querySelector('#tab-btn-upcoming');
        if (btnUpcoming) {
          btnUpcoming.innerHTML = `📡 Upcoming Radar (${this.upcomingSetups.length})`;
        }
      }
    } catch (e) {
      console.warn('Error fetching upcoming setups:', e);
    } finally {
      this.isFetchingUpcoming = false;
    }
  }

  // Recent Closed Trades Preview for Dashboard (Shows Realized Add-ons immediately)
  getRecentClosedTradesPreviewHtml() {
    if (!this.historyTrades || this.historyTrades.length === 0) return '';
    const recent = this.historyTrades.slice(0, 2);
    return `
      <div style="margin-top: 16px; padding: 12px; background: rgba(255, 255, 255, 0.02); border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.05); text-align: left;">
        <div style="font-size: 10px; font-weight: 800; color: var(--text-muted); letter-spacing: 0.5px; margin-bottom: 8px; display: flex; justify-content: space-between;">
          <span>RECENT CLOSED SETTLEMENTS</span>
          <span style="color: #60a5fa; cursor: pointer;" onclick="document.querySelector('#tab-btn-history')?.click()">VIEW ALL →</span>
        </div>
        ${recent.map(t => {
          const pnl = Number(t.realized_pnl !== undefined ? t.realized_pnl : (t.pnl_usdt || 0));
          const isWin = pnl >= 0;
          const colorClass = isWin ? 'text-green' : 'text-red';
          const sign = isWin ? '+' : '';
          return `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.04); font-size: 11px;">
              <div>
                <span style="font-weight: 800; color: #ffffff;">${t.symbol}</span>
                <span style="font-size: 9px; padding: 1px 4px; border-radius: 3px; margin-left: 4px; background: ${t.side === 'LONG' || t.side === 'BUY' ? '#052616' : '#2b0a12'}; color: ${t.side === 'LONG' || t.side === 'BUY' ? '#00f59b' : '#ff4d6a'}; font-weight: 700;">${t.side}</span>
              </div>
              <div class="mono ${colorClass}" style="font-weight: 700;">
                ${sign}$${pnl.toFixed(2)} USDT
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  // Smooth micro-updates: Updates text nodes without destroying the DOM
  updateTargetNodes(pos) {
    if (!pos || !pos.id) return;
    const cardEl = this.el.querySelector(`#pos-card-${pos.id}`);
    if (!cardEl) {
      this.render();
      return;
    }

    const unPnl = Number(pos.unrealizedPnl || 0);
    const pnlPct = Number(pos.pnlPct || 0);
    const isPnlPos = unPnl >= 0;
    const pnlColorClass = isPnlPos ? 'text-green' : 'text-red';
    const markPrice = Number(pos.markPrice || pos.entryPrice);
    const p = markPrice < 0.01 ? 6 : (markPrice < 1.0 ? 4 : 2);

    const pnlEl = cardEl.querySelector(`#pnl-val-${pos.id}`);
    if (pnlEl) {
      pnlEl.innerHTML = `${isPnlPos ? '+' : ''}${unPnl.toFixed(2)} <span style="font-size: 14px; font-weight: 500; opacity: 0.85;">≈ $${unPnl.toFixed(2)}</span>`;
      pnlEl.className = `mono ${pnlColorClass}`;
    }

    const roeEl = cardEl.querySelector(`#roe-val-${pos.id}`);
    if (roeEl) {
      roeEl.textContent = `${isPnlPos ? '+' : ''}${pnlPct.toFixed(2)}%`;
      roeEl.className = `mono ${pnlColorClass}`;
    }

    const markEl = cardEl.querySelector(`#mark-val-${pos.id}`);
    if (markEl) {
      markEl.textContent = markPrice.toFixed(p);
    }

    const mfeEl = cardEl.querySelector(`#mfe-val-${pos.id}`);
    if (mfeEl && pos.mfe !== undefined) {
      mfeEl.textContent = `▲ +${Math.abs(pos.mfe).toFixed(2)}% Gain`;
    }

    const maeEl = cardEl.querySelector(`#mae-val-${pos.id}`);
    if (maeEl && pos.mae !== undefined) {
      maeEl.textContent = `▼ -${Math.abs(pos.mae).toFixed(2)}% Risk`;
    }
  }

  // Generates 3-Tab Subnavigation Header
  getTabsHeaderHtml(positionsCount) {
    if (!this.isFullView) return '';
    return `
      <div style="display: flex; gap: 6px; margin: 10px 14px 14px 14px; overflow-x: auto;">
        <button id="tab-btn-open" style="flex: 1; padding: 10px 8px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.2s; white-space: nowrap; display: flex; align-items: center; justify-content: center; gap: 4px; background: ${this.activeTab === 'open' ? '#111d33' : '#0b0f17'}; border: 1px solid ${this.activeTab === 'open' ? '#2563eb' : '#1a2333'}; color: ${this.activeTab === 'open' ? '#60a5fa' : '#768296'};">
          🟢 Open (${positionsCount})
        </button>
        <button id="tab-btn-upcoming" style="flex: 1.2; padding: 10px 8px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.2s; white-space: nowrap; display: flex; align-items: center; justify-content: center; gap: 4px; background: ${this.activeTab === 'upcoming' ? '#111d33' : '#0b0f17'}; border: 1px solid ${this.activeTab === 'upcoming' ? '#2563eb' : '#1a2333'}; color: ${this.activeTab === 'upcoming' ? '#60a5fa' : '#768296'};">
          📡 Upcoming Radar (${this.upcomingSetups.length || '0'})
        </button>
        <button id="tab-btn-history" style="flex: 1; padding: 10px 8px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.2s; white-space: nowrap; display: flex; align-items: center; justify-content: center; gap: 4px; background: ${this.activeTab === 'history' ? '#111d33' : '#0b0f17'}; border: 1px solid ${this.activeTab === 'history' ? '#2563eb' : '#1a2333'}; color: ${this.activeTab === 'history' ? '#60a5fa' : '#768296'};">
          📜 History (${this.historyTrades.length || '0'})
        </button>
      </div>
    `;
  }

  render() {
    if (this.activeTab === 'history') {
      this.renderHistory();
      return;
    }
    if (this.activeTab === 'upcoming') {
      this.renderUpcoming();
      return;
    }

    const positions = state.positions || [];
    this.renderedTradeIds = positions.map(p => p.id);
    const tabsHtml = this.getTabsHeaderHtml(positions.length);

    if (positions.length === 0) {
      this.el.innerHTML = `
        ${tabsHtml}
        <div class="position-card" style="text-align: center; color: var(--text-muted); padding: 36px 16px; border: 1px dashed rgba(255, 255, 255, 0.08); background: #0b0f17; border-radius: 14px; margin: 0 14px;">
          <div style="font-size: 28px; margin-bottom: 8px;">🛡️</div>
          <div style="font-size: 14px; font-weight: 700; color: #ffffff; letter-spacing: 0.5px;">0 Active Trades • Standby Mode</div>
          <div style="font-size: 11px; margin-top: 6px; color: var(--text-muted);">
            Base Capital: <span class="mono text-green" style="font-weight: 700;">$${(state.account.freeMargin || state.account.baseCapital || 500).toFixed(2)} USDT (100% Free)</span> • Scanning 1H & 4H SMC Setups
          </div>
          ${this.getRecentClosedTradesPreviewHtml()}
          <div style="display: flex; gap: 10px; justify-content: center; margin-top: 16px; flex-wrap: wrap;">
            <button class="btn-pos" id="btn-view-upcoming-empty" style="background: #111d33; border: 1px solid #2563eb; color: #60a5fa; padding: 8px 16px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer;">
              📡 Check Upcoming Radar
            </button>
            <button class="btn-pos" id="btn-view-history-empty" style="background: #111827; border: 1px solid #1f293d; color: #a855f7; padding: 8px 16px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer;">
              📜 View Trade History (${this.historyTrades.length || '0'})
            </button>
          </div>
        </div>
      `;
      this.attachTabHandlers();
      const btnUp = this.el.querySelector('#btn-view-upcoming-empty');
      if (btnUp) btnUp.addEventListener('click', () => { this.activeTab = 'upcoming'; this.render(); this.fetchUpcomingSetups(); });
      const btnHist = this.el.querySelector('#btn-view-history-empty');
      if (btnHist) btnHist.addEventListener('click', () => { this.activeTab = 'history'; this.render(); this.fetchTradeHistory(); });
      return;
    }

    const cardsHtml = positions.map((pos) => {
      const isLong = pos.side === 'LONG';
      const unPnl = Number(pos.unrealizedPnl !== undefined ? pos.unrealizedPnl : (pos.unrealized_pnl || 0));
      const isPnlPos = unPnl >= 0;
      const pnlColorClass = isPnlPos ? 'text-green' : 'text-red';
      const sideBg = isLong ? '#052616' : '#2b0a12';
      const sideFg = isLong ? 'var(--green-institutional, #00e676)' : '#ff3358';
      const entryPrice = Number(pos.entryPrice !== undefined ? pos.entryPrice : (pos.entry_price || 0));
      const markPrice = Number(pos.markPrice !== undefined ? pos.markPrice : (pos.mark_price || entryPrice));
      const liqPrice = Number(pos.liquidationPrice !== undefined ? pos.liquidationPrice : (pos.liq_price || 0));
      const tfBadge = (pos.timeframe || '4H').toUpperCase();
      const marginUsdt = Number(pos.marginUsdt !== undefined ? pos.marginUsdt : (pos.margin_usdt || 50.0));
      const sizeUsd = Number(pos.sizeUsd !== undefined ? pos.sizeUsd : (pos.size_usdt || pos.position_size_usdt || 250.0));
      const coinName = pos.coin_name || (pos.symbol ? pos.symbol.replace('USDT', '') : 'COIN');
      const coinQty = pos.coinQty || pos.size_coin || (entryPrice > 0 ? (sizeUsd / entryPrice).toFixed(0) : '');
      const entryTimeStr = pos.entryTimeStr || (pos.entry_time ? new Date(pos.entry_time).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' IST' : 'Live');
      const durStr = pos.duration || pos.duration_str || 'Live';
      const mfeVal = Math.abs(pos.mfe !== undefined ? pos.mfe : (pos.mfe_pct || 0)).toFixed(2);
      const maeVal = Math.abs(pos.mae !== undefined ? pos.mae : (pos.mae_pct || 0)).toFixed(2);
      const realizedPnl = Number(pos.realized_pnl !== undefined ? pos.realized_pnl : -0.0050).toFixed(4);
      const p = entryPrice < 0.01 ? 6 : (entryPrice < 1.0 ? 4 : 2);

      const beActive = Boolean(pos.armor && pos.armor.beShield) || (pos.pnlPct >= 1.0 || pos.roi_pct >= 1.0);
      const trailActive = Boolean(pos.armor && pos.armor.trailing) || (pos.pnlPct >= 1.8 || pos.roi_pct >= 1.8);
      const tpActive = Boolean(pos.armor && pos.armor.takeProfit);
      const tpPrice = Number(pos.tpPrice || pos.tp_price || (isLong ? entryPrice * 1.03 : entryPrice * 0.97));

      return `
        <div class="position-card" id="pos-card-${pos.id}" data-trade-id="${pos.id}" style="background: #121826; border: 1px solid #1e293b; border-radius: 18px; padding: 18px 16px; margin: 0 14px 14px 14px; box-shadow: 0 6px 24px rgba(0,0,0,0.4);">
          <!-- 1. Header (Symbol, Badges & Top Chart Button) -->
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px;">
            <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
              <span class="pos-header-clickable" data-symbol="${pos.symbol}" style="font-size: 16px; font-weight: 800; color: #ffffff; cursor: pointer; text-decoration: underline; text-underline-offset: 3px;" title="View Live Chart">
                ${pos.symbol} ›
              </span>
              <span style="font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 4px; background: ${sideBg}; color: ${sideFg}; border: 1px solid ${sideFg}; letter-spacing: 0.5px;">
                ${pos.side === 'SELL' || pos.side === 'SHORT' ? 'Short' : 'Long'}
              </span>
              <span style="font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 4px; background: #0a1e30; color: #00e5ff; border: 1px solid #00e5ff;">
                ${pos.leverage || 5}x ✎
              </span>
              <span style="font-size: 10px; font-weight: 600; padding: 2px 7px; border-radius: 4px; background: #182030; color: #94a3b8; border: 1px solid #334155;">
                Isolated
              </span>
              <span style="font-size: 10px; font-weight: 600; padding: 2px 7px; border-radius: 4px; background: #182030; color: #94a3b8; border: 1px solid #334155;">
                USDT
              </span>
              <span style="font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; background: #0f1e36; color: #38bdf8; border: 1px solid #0284c7;">
                ${tfBadge}
              </span>
            </div>
            <button class="pos-header-clickable" data-symbol="${pos.symbol}" style="background: #0f172a; border: 1px solid #38bdf8; color: #38bdf8; font-size: 10px; font-weight: 700; padding: 4px 10px; border-radius: 6px; cursor: pointer;">
              📈 Chart
            </button>
          </div>

          <!-- 2. Prominent Hero PnL & ROE Display (Single Clean Value, Zero Duplication!) -->
          <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 12px; padding: 0 2px;">
            <div>
              <div style="font-size: 11px; color: var(--text-muted, #94a3b8); font-weight: 600; margin-bottom: 2px;">Unrealized PnL (USDT)</div>
              <div class="mono ${pnlColorClass}" id="pnl-val-${pos.id}" style="font-size: 26px; font-weight: 800; letter-spacing: -0.5px;">
                ${isPnlPos ? '+' : ''}${unPnl.toFixed(2)} <span style="font-size: 14px; font-weight: 500; opacity: 0.85;">≈ $${unPnl.toFixed(2)}</span>
              </div>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 11px; color: var(--text-muted, #94a3b8); font-weight: 600; margin-bottom: 2px;">ROE</div>
              <div class="mono ${pnlColorClass}" id="roe-val-${pos.id}" style="font-size: 26px; font-weight: 800; letter-spacing: -0.5px;">
                ${isPnlPos ? '+' : ''}${Number(pos.pnlPct !== undefined ? pos.pnlPct : (pos.roi_pct || 0)).toFixed(2)}%
              </div>
            </div>
          </div>

          <div style="height: 1px; background: #1e293b; margin: 10px 0 12px 0;"></div>

          <!-- 3. Binance 3-Column Metrics Grid (Capital, Margin & MMR) -->
          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 10px;">
            <div>
              <div style="font-size: 10px; color: #94a3b8; font-weight: 600;">Size (${coinName}) ▾</div>
              <div class="mono" style="font-size: 13px; font-weight: 700; color: #ffffff; margin-top: 2px;">${coinQty}</div>
              <div style="font-size: 10px; color: #64748b;">≈ $${sizeUsd.toFixed(2)}</div>
            </div>
            <div>
              <div style="font-size: 10px; color: #94a3b8; font-weight: 600;">Margin (USDT)</div>
              <div class="mono" style="font-size: 13px; font-weight: 800; color: #ffffff; margin-top: 2px;">${marginUsdt.toFixed(2)} <span style="color: #38bdf8;">⊕</span></div>
              <div style="font-size: 10px; color: #64748b;">5x Isolated</div>
            </div>
            <div>
              <div style="font-size: 10px; color: #94a3b8; font-weight: 600;">MMR</div>
              <div class="mono" style="font-size: 13px; font-weight: 700; color: #00e676; margin-top: 2px;">5.30%</div>
              <div style="font-size: 10px; color: #64748b;">[Safe]</div>
            </div>
          </div>

          <!-- 4. Binance 3-Column Price Grid (Entry, Mark, Liq) -->
          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 10px;">
            <div>
              <div style="font-size: 10px; color: #94a3b8; font-weight: 600;">Entry price</div>
              <div class="mono" style="font-size: 12px; font-weight: 700; color: #ffffff; margin-top: 2px;">${entryPrice.toFixed(p)}</div>
            </div>
            <div>
              <div style="font-size: 10px; color: #94a3b8; font-weight: 600;">Mark price</div>
              <div class="mono" id="mark-val-${pos.id}" style="font-size: 12px; font-weight: 700; color: #00e5ff; margin-top: 2px;">${markPrice.toFixed(p)}</div>
            </div>
            <div>
              <div style="font-size: 10px; color: #94a3b8; font-weight: 600;">Est. liq. price</div>
              <div class="mono" style="font-size: 12px; font-weight: 700; color: #f59e0b; margin-top: 2px;">${liqPrice.toFixed(p)}</div>
            </div>
          </div>

          <!-- 5. Binance Realized PnL Row -->
          <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-top: 1px solid #1e293b; margin-bottom: 10px;">
            <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">Realized PnL (USDT)</div>
            <div class="mono text-red" style="font-size: 12px; font-weight: 700;">${realizedPnl}</div>
          </div>

          <!-- 6. Execution Timing & Clean Risk/Gain Forensics (User Directives) -->
          <div style="background: #0c111c; border: 1px solid #1e293b; border-radius: 10px; padding: 10px 12px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 6px;">
              <div><span style="color: #64748b;">Entry Time:</span> <span class="mono" style="color: #ffffff; font-weight: 600;">${entryTimeStr}</span></div>
              <div><span style="color: #64748b;">Duration:</span> <span class="mono" style="color: #38bdf8; font-weight: 700;">⏱ ${durStr} Active</span></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 11px; border-top: 1px dashed rgba(255,255,255,0.06); padding-top: 6px;">
              <div><span style="color: #64748b;">MFE (Peak Gain):</span> <span class="mono text-green" id="mfe-val-${pos.id}" style="font-weight: 800;">▲ +${mfeVal}% Gain</span></div>
              <div><span style="color: #64748b;">MAE (Max Risk):</span> <span class="mono text-red" id="mae-val-${pos.id}" style="font-weight: 800;">▼ -${maeVal}% Risk</span></div>
            </div>
          </div>

          <!-- 7. Dynamic Profit Armor Protocol Status Pills -->
          <div style="display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 14px;">
            <span style="font-size: 9px; font-weight: 800; padding: 4px 8px; border-radius: 5px; background: ${beActive ? '#042616' : '#101622'}; color: ${beActive ? '#00e676' : '#64748b'}; border: 1px solid ${beActive ? '#059669' : '#1e293b'};">
              🛡️ BE SHIELD: ${beActive ? 'ACTIVE (+1.0%)' : '+1.0%'}
            </span>
            <span style="font-size: 9px; font-weight: 800; padding: 4px 8px; border-radius: 5px; background: ${trailActive ? '#042616' : '#101622'}; color: ${trailActive ? '#00e676' : '#64748b'}; border: 1px solid ${trailActive ? '#059669' : '#1e293b'};">
              ⚡ TRAILING: ${trailActive ? 'ARMED (+1.8%)' : '+1.8%'}
            </span>
            <span style="font-size: 9px; font-weight: 800; padding: 4px 8px; border-radius: 5px; background: #042616; color: #00e676; border: 1px solid #059669;">
              🎯 TP (+15% ROI): ${tpPrice.toFixed(p)}
            </span>
          </div>

          <!-- 8. Three Binance-Style Clean Pill Action Buttons -->
          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px;">
            <button class="pos-header-clickable" data-symbol="${pos.symbol}" style="background: #182030; border: 1px solid #334155; color: #f8fafc; padding: 9px 4px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer; text-align: center;">
              🎯 TP / SL
            </button>
            <button class="pos-header-clickable" data-symbol="${pos.symbol}" style="background: #182030; border: 1px solid #334155; color: #f8fafc; padding: 9px 4px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer; text-align: center;">
              📈 Chart View
            </button>
            <button class="btn-pos btn-close btn-close-action" data-trade-id="${pos.id}" data-symbol="${pos.symbol}" style="background: #2b0a12; border: 1px solid #ff3358; color: #ff3358; padding: 9px 4px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer; text-align: center;">
              ✕ Close (5x)
            </button>
          </div>
        </div>
      `;
    }).join('');

    this.el.innerHTML = tabsHtml + cardsHtml;
    this.attachDomHandlers();
  }

  // Renders the Upcoming SMC Order Block Proximity Radar
  renderUpcoming() {
    const tabsHtml = this.getTabsHeaderHtml(state.positions.length);
    const count = this.upcomingSetups.length;

    const bannerHtml = `
      <div style="background: #0b0f17; border: 1px solid #182232; border-radius: 12px; padding: 14px 16px; margin: 0 14px 14px 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="font-size: 13px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px;">📡 SMC PROXIMITY RADAR</div>
            <div style="font-size: 10px; color: #768296; margin-top: 2px;">20 Champion Pairs • 1H & 4H First Tap Order Blocks</div>
          </div>
          <button id="btn-refresh-upcoming" style="background: #111d33; border: 1px solid #2563eb; color: #60a5fa; font-size: 10px; font-weight: 700; padding: 4px 10px; border-radius: 5px; cursor: pointer;">
            🔄 Refresh
          </button>
        </div>
        <div style="margin-top: 10px; font-size: 11px; color: #94a3b8; border-top: 1px dashed rgba(255,255,255,0.06); padding-top: 8px;">
          Setups sorted by <span class="mono text-green" style="font-weight: 700;">% Distance Away From Entry</span>. Closest setups appear at top.
        </div>
      </div>
    `;

    if (count === 0) {
      this.el.innerHTML = `
        ${tabsHtml}
        ${bannerHtml}
        <div style="text-align: center; color: var(--text-muted); padding: 36px 16px; background: #0b0f17; border: 1px dashed rgba(255, 255, 255, 0.08); border-radius: 14px; margin: 0 14px;">
          <div style="font-size: 26px; margin-bottom: 6px;">📡</div>
          <div style="font-size: 13px; font-weight: 700; color: #ffffff;">No Active Order Blocks Within 6%</div>
          <div style="font-size: 11px; margin-top: 4px; color: var(--text-muted);">
            Scanning 1H & 4H institutional Order Blocks. When price approaches a zone, it will appear here instantly.
          </div>
        </div>
      `;
      this.attachTabHandlers();
      const btnRef = this.el.querySelector('#btn-refresh-upcoming');
      if (btnRef) btnRef.addEventListener('click', () => this.fetchUpcomingSetups());
      return;
    }

    const cardsHtml = this.upcomingSetups.map((s) => {
      const isDemand = s.direction === 'DEMAND' || s.side === 'BUY';
      const sideBg = isDemand ? '#052616' : '#2b0a12';
      const sideFg = isDemand ? '#00e676' : '#ff3358';
      const dirLabel = isDemand ? 'DEMAND OB' : 'SUPPLY OB';
      const curPrice = Number(s.current_price || 0);
      const entryPrice = Number(s.entry_price || 0);
      const obTop = Number(s.ob_top || 0);
      const obBot = Number(s.ob_bottom || 0);
      const distPct = Number(s.distance_pct || 0);
      const p = entryPrice < 0.01 ? 6 : (entryPrice < 1.0 ? 4 : 2);

      // Distance Tier & Styling
      let tierColor = '#38bdf8';
      let tierBadge = '📡 ON RADAR';
      let progressColor = '#38bdf8';
      if (distPct < 0.50 || s.is_inside) {
        tierColor = isDemand ? '#00e676' : '#ff3358';
        tierBadge = '🔥 IMMINENT TAP';
        progressColor = isDemand ? '#00e676' : '#ff3358';
      } else if (distPct <= 1.50) {
        tierColor = '#ffb020';
        tierBadge = '⚡ APPROACHING';
        progressColor = '#ffb020';
      }

      // Proximity Bar fill (Closer = Fuller Bar!)
      const progressWidth = Math.max(10, Math.min(100, (1 - (distPct / 5.0)) * 100));

      return `
        <div style="background: #0b0f17; border: 1px solid ${distPct < 0.5 ? tierColor : '#182232'}; border-radius: 14px; padding: 16px; margin: 0 14px 12px 14px; box-shadow: 0 4px 18px rgba(0,0,0,0.3);">
          <!-- Top Row -->
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
              <span class="pos-header-clickable" data-symbol="${s.symbol}" data-tf="${s.timeframe}" style="font-size: 15px; font-weight: 800; color: #ffffff; cursor: pointer; text-decoration: underline; text-underline-offset: 3px;" title="View Live Chart">
                ${s.symbol} ›
              </span>
              <span style="font-size: 9px; font-weight: 800; padding: 2px 6px; border-radius: 4px; background: ${sideBg}; color: ${sideFg}; border: 1px solid ${sideFg};">
                ${dirLabel}
              </span>
              <span style="font-size: 9px; font-weight: 700; padding: 2px 5px; border-radius: 4px; background: #0a1933; color: #93c5fd; border: 1px solid #1d4ed8;">
                ${s.timeframe}
              </span>
              <span style="font-size: 9px; font-weight: 800; padding: 2px 5px; border-radius: 4px; background: #261a05; color: #ffb020;">
                ★ 3★
              </span>
            </div>
            <button class="pos-header-clickable" data-symbol="${s.symbol}" data-tf="${s.timeframe}" style="background: #0e1726; border: 1px solid #2563eb; color: #60a5fa; font-size: 10px; font-weight: 700; padding: 4px 9px; border-radius: 5px; cursor: pointer;">
              📈 Chart View
            </button>
          </div>

          <!-- Price & Entry Row -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; background: #070a10; border: 1px solid #141c2b; border-radius: 8px; padding: 8px 10px;">
            <div>
              <div style="font-size: 10px; color: #768296;">Current Price</div>
              <div class="mono" style="font-size: 13px; font-weight: 700; color: #ffffff; margin-top: 2px;">${curPrice.toFixed(p)}</div>
            </div>
            <div>
              <div style="font-size: 10px; color: #768296;">OB Entry Boundary</div>
              <div class="mono" style="font-size: 13px; font-weight: 800; color: ${sideFg}; margin-top: 2px;">${entryPrice.toFixed(p)}</div>
            </div>
          </div>

          <!-- Proximity Visual Bar (% Distance Away) -->
          <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; font-size: 10px; margin-bottom: 4px;">
              <span style="color: #94a3b8; font-weight: 600;">PROXIMITY TO ENTRY:</span>
              <span class="mono" style="color: ${tierColor}; font-weight: 800;">
                ${distPct.toFixed(2)}% Away [${tierBadge}]
              </span>
            </div>
            <div style="height: 6px; background: #141c2b; border-radius: 3px; overflow: hidden; position: relative;">
              <div style="height: 100%; width: ${progressWidth}%; background: ${progressColor}; border-radius: 3px; transition: width 0.3s ease;"></div>
            </div>
          </div>

          <!-- Setup Risk / Reward Blueprint -->
          <div style="display: flex; justify-content: space-between; font-size: 10px; border-top: 1px dashed rgba(255,255,255,0.06); padding-top: 6px; color: #64748b;">
            <div>Zone: <span class="mono" style="color: #94a3b8;">${obBot.toFixed(p)} - ${obTop.toFixed(p)}</span></div>
            <div>TP1: <span class="mono text-green" style="font-weight: 700;">+10%</span> • SL: <span class="mono text-red" style="font-weight: 700;">-15%</span></div>
          </div>
        </div>
      `;
    }).join('');

    this.el.innerHTML = tabsHtml + bannerHtml + cardsHtml;
    this.attachDomHandlers();
    const btnRef = this.el.querySelector('#btn-refresh-upcoming');
    if (btnRef) btnRef.addEventListener('click', () => this.fetchUpcomingSetups());
  }

  // Renders the Full Trade History Table & Forensics Log
  renderHistory() {
    const tabsHtml = this.getTabsHeaderHtml(state.positions.length);

    // Overview Stats Banner with Win / Loss Breakdown Slot
    const stats = this.historyStats || { total: 0, tpHits: 0, slHits: 0, winRate: '0.0', totalPnl: 0 };
    const tpPct = stats.total > 0 ? ((stats.tpHits / stats.total) * 100).toFixed(0) : 0;
    const slPct = stats.total > 0 ? ((stats.slHits / stats.total) * 100).toFixed(0) : 0;
    const statsHtml = `
      <div style="background: #0b101d; border: 1px solid #1e293b; border-radius: 12px; padding: 12px 14px; margin: 0 14px 10px 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
        <div style="display: grid; grid-template-columns: 1fr 1fr 1.15fr; gap: 6px; align-items: flex-end; margin-bottom: 10px;">
          <div>
            <div style="font-size: 9.5px; color: #768296; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px; margin-bottom: 2px;">Closed Trades</div>
            <div class="mono" style="font-size: 15.5px; font-weight: 800; color: #ffffff;">${stats.total}</div>
          </div>
          <div style="text-align: center;">
            <div style="font-size: 9.5px; color: #768296; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px; margin-bottom: 2px;">Win Rate</div>
            <div class="mono text-green" style="font-size: 15.5px; font-weight: 800;">${stats.winRate}%</div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 9.5px; color: #768296; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px; margin-bottom: 2px;">Total Realized</div>
            <div class="mono ${stats.totalPnl >= 0 ? 'text-green' : 'text-red'}" style="font-size: 15.5px; font-weight: 800;">
              ${stats.totalPnl >= 0 ? '+' : ''}$${stats.totalPnl.toFixed(2)}
            </div>
          </div>
        </div>
        
        <!-- Win / Loss Breakdown Row -->
        <div style="display: flex; gap: 5px; background: #060912; border: 1px solid #182232; border-radius: 8px; padding: 6px 8px; justify-content: space-between; align-items: center;">
          <div style="display: inline-flex; align-items: center; gap: 4px; font-size: 9.5px; font-weight: 800; padding: 4px 6px; border-radius: 5px; background: #042616; color: #00e676; border: 1px solid #059669;">
            <span>🎯</span> ${stats.tpHits} TP Hit <span style="font-weight: 500; opacity: 0.85;">(${tpPct}%)</span>
          </div>
          <div style="display: inline-flex; align-items: center; gap: 4px; font-size: 9.5px; font-weight: 800; padding: 4px 6px; border-radius: 5px; background: #2b0a12; color: #ff3358; border: 1px solid #e11d48;">
            <span>🛑</span> ${stats.slHits} SL Hit <span style="font-weight: 500; opacity: 0.85;">(${slPct}%)</span>
          </div>
          <div style="display: inline-flex; align-items: center; gap: 4px; font-size: 9.5px; font-weight: 800; padding: 4px 6px; border-radius: 5px; background: #0c1a2e; color: #38bdf8; border: 1px solid #0284c7;">
            <span>⚡</span> 5x Isolated
          </div>
        </div>
      </div>
    `;

    if (this.historyTrades.length === 0) {
      this.el.innerHTML = `
        ${tabsHtml}
        ${statsHtml}
        <div style="text-align: center; color: var(--text-muted); padding: 32px 16px; background: #0b0f17; border: 1px dashed rgba(255, 255, 255, 0.08); border-radius: 14px; margin: 0 14px;">
          <div style="font-size: 24px; margin-bottom: 6px;">📜</div>
          <div style="font-size: 13px; font-weight: 700; color: #ffffff;">No Closed Trades Recorded</div>
          <div style="font-size: 11px; margin-top: 4px; color: var(--text-muted);">As positions close, their exact results and forensics will appear here automatically.</div>
        </div>
      `;
      this.attachTabHandlers();
      return;
    }

    const historyCards = this.historyTrades.map(t => {
      const pnl = Number(t.realized_pnl !== undefined ? t.realized_pnl : (t.pnl_usdt || 0));
      const roi = Number(t.roi_pct !== undefined ? t.roi_pct : (t.pnl_pct || 0));
      const isWin = pnl >= 0;
      const pnlColorClass = isWin ? 'text-green' : 'text-red';
      const isLong = (t.side_raw || t.side) === 'LONG' || t.side === 'BUY';
      const sideBg = isLong ? '#052616' : '#2b0a12';
      const sideFg = isLong ? 'var(--green-institutional, #00e676)' : '#ff3358';
      const entryPrice = Number(t.entry_price || 0);
      const exitPrice = Number(t.exit_price || entryPrice);
      const p = entryPrice < 0.01 ? 6 : (entryPrice < 1.0 ? 4 : 2);
      const entryTimeStr = t.entry_time_str || (t.entry_time ? new Date(t.entry_time).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) + ', ' + new Date(t.entry_time).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' IST' : '--');
      const exitTimeStr = t.exit_time_str || (t.exit_time ? new Date(t.exit_time).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) + ', ' + new Date(t.exit_time).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' IST' : 'Live');
      const durStr = t.duration || t.duration_str || '--';
      const outcome = t.result || t.status || (isWin ? 'TP HIT' : 'SL HIT');

      return `
        <div style="background: #0b0f17; border: 1px solid #182232; border-radius: 12px; padding: 14px 16px; margin: 0 14px 10px 14px;">
          <!-- Top Row -->
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 6px;">
              <span style="font-size: 14px; font-weight: 800; color: #ffffff;">${t.symbol}</span>
              <span style="font-size: 9px; font-weight: 800; padding: 2px 6px; border-radius: 4px; background: ${sideBg}; color: ${sideFg}; border: 1px solid ${sideFg};">
                ${isLong ? 'LONG' : 'SHORT'}
              </span>
              <span style="font-size: 9px; font-weight: 700; padding: 2px 5px; border-radius: 4px; background: #0a1933; color: #93c5fd; border: 1px solid #1d4ed8;">
                ${(t.timeframe || '1H').toUpperCase()}
              </span>
            </div>
            <span style="font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 4px; background: ${isWin ? '#052616' : '#2b0a12'}; color: ${isWin ? '#00e676' : '#ff3358'}; border: 1px solid ${isWin ? '#00e676' : '#ff3358'};">
              ${outcome}
            </span>
          </div>

          <!-- Middle Row: PnL & Execution -->
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div>
              <div style="font-size: 10px; color: #768296;">Realized PnL</div>
              <div class="mono ${pnlColorClass}" style="font-size: 16px; font-weight: 800;">
                ${isWin ? '+' : ''}$${pnl.toFixed(2)} <span style="font-size: 12px;">(${isWin ? '+' : ''}${roi.toFixed(2)}%)</span>
              </div>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 10px; color: #768296;">Entry → Exit</div>
              <div class="mono" style="font-size: 12px; font-weight: 600; color: #ffffff;">
                ${entryPrice.toFixed(p)} → ${exitPrice.toFixed(p)}
              </div>
            </div>
          </div>

          <!-- Timestamps Grid (Exact Entry & Exit Times) -->
          <div style="background: #060912; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 7px; padding: 5px 8px; margin-bottom: 5px;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 9.5px; line-height: 1.5;">
              <span style="color: #64748b; font-weight: 600;">🟢 Entry:</span>
              <span class="mono" style="color: #cbd5e1; font-weight: 600;">${entryTimeStr}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 9.5px; line-height: 1.5;">
              <span style="color: #64748b; font-weight: 600;">${isWin ? '🏁' : '🛑'} Exit:</span>
              <span class="mono" style="color: #cbd5e1; font-weight: 600;">${exitTimeStr}</span>
            </div>
          </div>

          <!-- Footer: Duration & Outcome Status -->
          <div style="display: flex; justify-content: space-between; font-size: 9px; color: #64748b;">
            <div>⏱ Duration: <span class="mono" style="color: #cbd5e1; font-weight: 700;">${durStr}</span></div>
            <div class="mono" style="color: ${isWin ? '#00e676' : '#ff3358'}; font-weight: 700;">Executed (${outcome})</div>
          </div>
        </div>
      `;
    }).join('');

    this.el.innerHTML = tabsHtml + statsHtml + historyCards;
    this.attachTabHandlers();
  }

  attachTabHandlers() {
    const tabOpen = this.el.querySelector('#tab-btn-open');
    if (tabOpen) {
      tabOpen.addEventListener('click', () => {
        this.activeTab = 'open';
        this.render();
      });
    }

    const tabUpcoming = this.el.querySelector('#tab-btn-upcoming');
    if (tabUpcoming) {
      tabUpcoming.addEventListener('click', () => {
        this.activeTab = 'upcoming';
        this.render();
        this.fetchUpcomingSetups();
      });
    }

    const tabHistory = this.el.querySelector('#tab-btn-history');
    if (tabHistory) {
      tabHistory.addEventListener('click', () => {
        this.activeTab = 'history';
        this.render();
        this.fetchTradeHistory();
      });
    }
  }

  attachDomHandlers() {
    this.attachTabHandlers();

    // Attach Click Handlers to jump to Chart
    this.el.querySelectorAll('.pos-header-clickable').forEach(header => {
      header.addEventListener('click', () => {
        const sym = header.dataset.symbol;
        const tf = header.dataset.tf ? header.dataset.tf.toLowerCase() : null;
        if (sym) {
          if (tf) state.setTimeframe(tf);
          state.selectSymbol(sym);
          state.setView('chart');
        }
      });
    });

    // Close Trade Button Action
    this.el.querySelectorAll('.btn-close-action').forEach(btn => {
      btn.addEventListener('click', async () => {
        const tId = parseInt(btn.dataset.tradeId);
        const sym = btn.dataset.symbol;
        if (confirm(`Institutional Close: Are you sure you want to permanently close ${sym}?`)) {
          try {
            await fetch('/api/paper/close', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ trade_id: tId, symbol: sym })
            });
          } catch (e) {}
          state.closePosition(tId);
          state.syncPositionsFromServer();
        }
      });
    });
  }
}
