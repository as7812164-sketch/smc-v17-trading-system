"""
HERMES 3.5 DUAL-TIER WEEKLY MONITOR & LOSS AUTOPSY ENGINE
=========================================================
Tracks and generates daily and 7-day rolling performance audits:
1. Trade execution counts, Win Rate %, Net P&L USDT, Compounding growth.
2. Long vs Short accuracy breakdown.
3. MAE (Maximum Adverse Excursion) & MFE (Maximum Favorable Excursion) forensics.
4. Automatic Loss Autopsy & Root-Cause Analysis (Why SL hit?).
5. Persistent Markdown Artifact generation for user audits.
"""

import os
import time
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from database.db import get_connection

logger = logging.getLogger("WeeklyMonitor")
IST = timezone(timedelta(hours=5, minutes=30))
ARTIFACT_DIR = r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c"


class Hermes35WeeklyMonitor:
    def __init__(self):
        self.version = "HERMES_3.5_DUAL_TIER_SNIPER"

    def backfill_missing_autopsies(self) -> int:
        """
        Backfills loss autopsy records for any closed trade in paper_trades that had SL_HIT or negative PnL
        but does not have an entry in trade_autopsy.
        """
        now_ms = int(time.time() * 1000)
        with get_connection() as conn:
            missing = conn.execute("""
                SELECT pt.* FROM paper_trades pt
                LEFT JOIN trade_autopsy ta ON pt.id = ta.trade_id
                WHERE ta.id IS NULL 
                  AND (pt.status = 'SL_HIT' OR (pt.pnl_usdt IS NOT NULL AND pt.pnl_usdt < 0))
                ORDER BY pt.id ASC
            """).fetchall()

            count = 0
            for row in missing:
                t = dict(row)
                trade_id = t.get("id")
                sym = str(t.get("symbol", "")).upper()
                side = str(t.get("side", "")).upper()
                tf = str(t.get("timeframe") or "4h").lower()
                entry_p = float(t.get("entry_price") or 0.0)
                exit_p = float(t.get("exit_price") or entry_p)
                pnl_usdt = float(t.get("pnl_usdt") or 0.0)
                roe_pct = float(t.get("roi_pct") or t.get("pnl_pct") or 0.0)
                mae_pct = float(t.get("mae_pct") or 0.0)
                mfe_pct = float(t.get("mfe_pct") or 0.0)
                duration_str = str(t.get("duration_str") or "N/A")
                created_at = t.get("exit_time") or now_ms

                # Post-mortem categorization based on excursion forensics
                if mfe_pct >= 4.5:
                    loss_cat = "PRE_TP_REVERSAL"
                    diag = f"Runner Chop: Trade achieved peak favorable excursion of +{mfe_pct:.1f}% ROE towards TP, but reversed into SL before final mitigation."
                elif mae_pct >= 14.0:
                    loss_cat = "LIQUIDATION_WICK"
                    diag = f"Market-Maker Stop Hunt: Aggressive volatility wick swept zone stop barrier (MAE -{mae_pct:.1f}% ROE) before stabilizing."
                elif mfe_pct < 0.8:
                    loss_cat = "MOMENTUM_PENETRATION"
                    diag = f"Zero Absorption: Mitigation candle broke through 50% Mean Threshold without counter-liquidity response (MFE +{mfe_pct:.1f}%)."
                else:
                    loss_cat = "STRUCTURAL_STOP"
                    diag = f"Standard SMC Invalidation: Order block invalidated by structural trend shift (MAE -{mae_pct:.1f}%, MFE +{mfe_pct:.1f}%)."

                conn.execute("""
                INSERT INTO trade_autopsy (
                    trade_id, symbol, side, timeframe, entry_price, exit_price,
                    pnl_usdt, roe_pct, mae_pct, mfe_pct, duration_str,
                    btc_macro_state, order_flow_delta, loss_category, autopsy_diagnosis, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_id, sym, side, tf, entry_p, exit_p,
                    pnl_usdt, roe_pct, mae_pct, mfe_pct, duration_str,
                    "Historical Audit Backfill", 0.0, loss_cat, diag, created_at
                ))
                conn.execute("UPDATE paper_trades SET autopsy_diagnosis = ? WHERE id = ?", (diag, trade_id))
                count += 1
            if count > 0:
                conn.commit()
                logger.info(f"🩺 Backfilled {count} missing trade autopsy records.")
            return count

    async def record_loss_autopsy(self, trade: Dict[str, Any], exit_price: float, outcome: str) -> Dict[str, Any]:
        """
        Executes instant forensic post-mortem when a trade exits with SL_HIT or negative PnL.
        Identifies WHY the Stop Loss was triggered.
        """
        now_ms = int(time.time() * 1000)
        trade_id = trade.get("id")
        sym = str(trade.get("symbol", "")).upper()
        side = str(trade.get("side", "")).upper()
        tf = str(trade.get("timeframe") or "4h").lower()
        entry_p = float(trade.get("entry_price") or 0.0)
        tp_p = float(trade.get("tp_price") or 0.0)
        sl_p = float(trade.get("sl_price") or 0.0)
        pnl_usdt = float(trade.get("pnl_usdt") or 0.0)
        roe_pct = float(trade.get("roi_pct") or trade.get("pnl_pct") or 0.0)
        mae_pct = float(trade.get("mae_pct") or 0.0)
        mfe_pct = float(trade.get("mfe_pct") or 0.0)
        duration_str = str(trade.get("duration_str") or "N/A")

        # 1. Fetch BTC Macro Context around exit time
        btc_change_str = "BTC Stable (< 1.0% move)"
        btc_dump_or_pump = 0.0
        try:
            from feed.binance_feed import binance_feed
            btc_candles = await binance_feed.fetch_klines("BTCUSDT", interval="4h", limit=3)
            if btc_candles and len(btc_candles) >= 2:
                last_c = btc_candles[-1]
                prev_c = btc_candles[-2]
                pct_move = (last_c["close"] - prev_c["open"]) / prev_c["open"] * 100.0
                btc_dump_or_pump = pct_move
                if pct_move <= -1.8:
                    btc_change_str = f"BTC Macro Dump ({pct_move:+.2f}%)"
                elif pct_move >= 1.8:
                    btc_change_str = f"BTC Macro Pump ({pct_move:+.2f}%)"
                else:
                    btc_change_str = f"BTC Neutral ({pct_move:+.2f}%)"
        except Exception as ex:
            logger.debug(f"Could not fetch live BTC context: {ex}")

        # 2. Determine Loss Root Cause Category & Detailed Explanation
        loss_category = "STRUCTURAL_FAILURE"
        diagnosis = ""

        # Case A: High MFE before reversal (Reached significant profit before hitting SL)
        if mfe_pct >= 5.5:  # Over +1.1% price move into profit (@ 5x = 5.5% ROE)
            loss_category = "PRE_TP_REVERSAL"
            diagnosis = (
                f"Runner Chop: Trade moved into peak profit of MFE +{mfe_pct:.1f}% ROE towards TP, "
                f"but failed to complete full target before institutional counter-flow reversed into SL."
            )
        # Case B: BTC Macro Correlation Pressure
        elif (side in ("BUY", "LONG") and btc_dump_or_pump <= -1.5) or (side in ("SELL", "SHORT") and btc_dump_or_pump >= 1.5):
            loss_category = "BTC_CAUSAL_SWEEP"
            diagnosis = (
                f"King Bitcoin Drag: Altcoin setup structure was valid, but King BTC experienced a "
                f"sharp {btc_change_str} that overwhelmed altcoin orderbook liquidity."
            )
        # Case C: Extreme Liquidation Wick (Deep sweep beyond structural boundary)
        elif mae_pct >= 14.0:
            loss_category = "LIQUIDATION_WICK"
            diagnosis = (
                f"Market-Maker Stop Hunt: Aggressive liquidation wick penetrated zone boundary "
                f"(MAE -{mae_pct:.1f}% ROE) before market stabilized."
            )
        # Case D: Instant Adverse Momentum (No reaction at OB)
        elif mfe_pct < 1.0:
            loss_category = "MOMENTUM_PENETRATION"
            diagnosis = (
                f"Zero Absorption: Mitigation candle lacked buyers/sellers at Mean Threshold (MFE only +{mfe_pct:.1f}%), "
                f"resulting in immediate structural failure."
            )
        else:
            loss_category = "STRUCTURAL_STOP"
            diagnosis = (
                f"Standard SMC Invalidation: Price retraced beyond 50% Mean Threshold buffer. "
                f"Normal statistical distribution (MAE -{mae_pct:.1f}%, MFE +{mfe_pct:.1f}%)."
            )

        # 3. Save into trade_autopsy table
        autopsy_record = {
            "trade_id": trade_id,
            "symbol": sym,
            "side": side,
            "timeframe": tf,
            "entry_price": entry_p,
            "exit_price": exit_price,
            "pnl_usdt": pnl_usdt,
            "roe_pct": roe_pct,
            "mae_pct": mae_pct,
            "mfe_pct": mfe_pct,
            "duration_str": duration_str,
            "btc_macro_state": btc_change_str,
            "order_flow_delta": 0.0,
            "loss_category": loss_category,
            "autopsy_diagnosis": diagnosis,
            "created_at": now_ms
        }

        with get_connection() as conn:
            conn.execute("""
            INSERT INTO trade_autopsy (
                trade_id, symbol, side, timeframe, entry_price, exit_price,
                pnl_usdt, roe_pct, mae_pct, mfe_pct, duration_str,
                btc_macro_state, order_flow_delta, loss_category, autopsy_diagnosis, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_id, sym, side, tf, entry_p, exit_price,
                pnl_usdt, roe_pct, mae_pct, mfe_pct, duration_str,
                btc_change_str, 0.0, loss_category, diagnosis, now_ms
            ))

            # Also update paper_trades column
            if trade_id:
                conn.execute("UPDATE paper_trades SET autopsy_diagnosis = ? WHERE id = ?", (diagnosis, trade_id))

            conn.commit()

        logger.info(f"🩺 [LOSS AUTOPSY SAVED] #{trade_id} {sym} {side}: {loss_category} -> {diagnosis}")
        return autopsy_record

    def get_daily_report(self, target_date_str: Optional[str] = None) -> Dict[str, Any]:
        """Fetches daily summary for a specific day (YYYY-MM-DD IST) or today."""
        self.backfill_missing_autopsies()
        now_dt = datetime.now(IST)
        day_str = target_date_str or now_dt.strftime("%Y-%m-%d")

        # Start and end of day in UTC ms
        day_start = datetime.strptime(day_str, "%Y-%m-%d").replace(tzinfo=IST)
        start_ms = int(day_start.timestamp() * 1000)
        end_ms = start_ms + (24 * 3600 * 1000)

        with get_connection() as conn:
            # Closed trades settled today
            rows = conn.execute("""
            SELECT * FROM paper_trades 
            WHERE exit_time >= ? AND exit_time < ? AND status != 'OPEN'
            ORDER BY exit_time ASC
            """, (start_ms, end_ms)).fetchall()
            closed_trades = [dict(r) for r in rows]

            # Open trades currently active
            open_rows = conn.execute("SELECT * FROM paper_trades WHERE status = 'OPEN' ORDER BY entry_time DESC").fetchall()
            open_trades = [dict(r) for r in open_rows]

            # Autopsies recorded today
            autopsy_rows = conn.execute("SELECT * FROM trade_autopsy WHERE created_at >= ? AND created_at < ? ORDER BY id DESC", (start_ms, end_ms)).fetchall()
            autopsies = [dict(r) for r in autopsy_rows]

        completed = [t for t in closed_trades if (t.get("pnl_usdt") is not None) or t.get("status") in ("TP_HIT", "SL_HIT", "MANUAL_CLOSED")]
        wins = sum(1 for t in completed if (t.get("pnl_usdt") or 0) > 0 or "TP" in str(t.get("status", "")))
        losses = sum(1 for t in completed if (t.get("pnl_usdt") or 0) < 0 or "SL" in str(t.get("status", "")))
        wr = (wins / (wins + losses) * 100.0) if (wins + losses) > 0 else (100.0 if wins > 0 else 0.0)
        tot_pnl = sum((t.get("pnl_usdt") or 0.0) for t in completed)

        return {
            "date": day_str,
            "strategy": self.version,
            "total_trades": len(completed),
            "wins": wins,
            "losses": losses,
            "win_rate": round(wr, 2),
            "net_pnl_usdt": round(tot_pnl, 2),
            "open_positions_count": len(open_trades),
            "open_positions": open_trades,
            "closed_trades": completed,
            "autopsies": autopsies
        }

    def get_weekly_report(self, days: int = 7) -> Dict[str, Any]:
        """Calculates rolling 7-day master forensic overview with MAE/MFE and SL autopsies."""
        self.backfill_missing_autopsies()
        now_ms = int(time.time() * 1000)
        since_ms = now_ms - (days * 24 * 3600 * 1000)

        with get_connection() as conn:
            # Closed trades in the last 7 days
            rows = conn.execute("""
            SELECT * FROM paper_trades 
            WHERE exit_time >= ? AND status != 'OPEN'
            ORDER BY exit_time ASC
            """, (since_ms,)).fetchall()
            all_trades = [dict(r) for r in rows]

            # Open positions
            open_rows = conn.execute("SELECT * FROM paper_trades WHERE status = 'OPEN' ORDER BY entry_time DESC").fetchall()
            open_trades = [dict(r) for r in open_rows]

            # Autopsies
            autopsy_rows = conn.execute("SELECT * FROM trade_autopsy WHERE created_at >= ? ORDER BY id DESC", (since_ms,)).fetchall()
            autopsies = [dict(r) for r in autopsy_rows]

            # Account balances
            acc_rows = conn.execute("SELECT * FROM paper_account").fetchall()
            accounts = [dict(r) for r in acc_rows]

        # Filter completed trades that represent real market activity
        completed_trades = [
            t for t in all_trades 
            if (t.get("pnl_usdt") is not None) 
            or t.get("status") in ("TP_HIT", "SL_HIT", "MANUAL_CLOSED")
        ]

        tot_trades = len(completed_trades)
        wins = sum(1 for t in completed_trades if (t.get("pnl_usdt") or 0) > 0 or "TP" in str(t.get("status", "")))
        losses = sum(1 for t in completed_trades if (t.get("pnl_usdt") or 0) < 0 or "SL" in str(t.get("status", "")))
        breakevens = tot_trades - wins - losses
        wr = (wins / (wins + losses) * 100.0) if (wins + losses) > 0 else (100.0 if wins > 0 else 0.0)

        long_trades = [t for t in completed_trades if str(t.get("side", "")).upper() in ("BUY", "LONG")]
        short_trades = [t for t in completed_trades if str(t.get("side", "")).upper() in ("SELL", "SHORT")]

        lw = sum(1 for t in long_trades if (t.get("pnl_usdt") or 0) > 0 or "TP" in str(t.get("status", "")))
        ll = sum(1 for t in long_trades if (t.get("pnl_usdt") or 0) < 0 or "SL" in str(t.get("status", "")))
        lwr = (lw / (lw + ll) * 100.0) if (lw + ll) > 0 else (100.0 if lw > 0 else 0.0)

        sw = sum(1 for t in short_trades if (t.get("pnl_usdt") or 0) > 0 or "TP" in str(t.get("status", "")))
        sl = sum(1 for t in short_trades if (t.get("pnl_usdt") or 0) < 0 or "SL" in str(t.get("status", "")))
        swr = (sw / (sw + sl) * 100.0) if (sw + sl) > 0 else (100.0 if sw > 0 else 0.0)

        # MAE and MFE averages across completed trades
        mae_list = [float(t.get("mae_pct") or 0.0) for t in completed_trades if t.get("mae_pct") is not None]
        mfe_list = [float(t.get("mfe_pct") or 0.0) for t in completed_trades if t.get("mfe_pct") is not None]
        avg_mae = (sum(mae_list) / len(mae_list)) if mae_list else 0.0
        avg_mfe = (sum(mfe_list) / len(mfe_list)) if mfe_list else 0.0

        net_pnl = sum((t.get("pnl_usdt") or 0.0) for t in completed_trades)
        gross_profit = sum((t.get("pnl_usdt") or 0.0) for t in completed_trades if (t.get("pnl_usdt") or 0.0) > 0)
        gross_loss = abs(sum((t.get("pnl_usdt") or 0.0) for t in completed_trades if (t.get("pnl_usdt") or 0.0) < 0))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

        # Accounts total equity
        total_balance = sum(float(a.get("current_balance") or 50.0) for a in accounts)
        total_vault = sum(float(a.get("vault_balance") or 0.0) for a in accounts)
        total_equity = total_balance + total_vault

        return {
            "period_days": days,
            "strategy": self.version,
            "generated_at": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
            "total_trades": tot_trades,
            "wins": wins,
            "losses": losses,
            "breakevens": breakevens,
            "win_rate": round(wr, 2),
            "profit_factor": profit_factor,
            "gross_profit_usdt": round(gross_profit, 2),
            "gross_loss_usdt": round(gross_loss, 2),
            "long_metrics": {
                "total": len(long_trades),
                "wins": lw,
                "losses": ll,
                "win_rate": round(lwr, 2)
            },
            "short_metrics": {
                "total": len(short_trades),
                "wins": sw,
                "losses": sl,
                "win_rate": round(swr, 2)
            },
            "avg_mae_pct": round(avg_mae, 2),
            "avg_mfe_pct": round(avg_mfe, 2),
            "net_pnl_usdt": round(net_pnl, 2),
            "total_portfolio_equity": round(total_equity, 2),
            "open_positions_count": len(open_trades),
            "open_positions": open_trades,
            "closed_trades": completed_trades,
            "autopsies": autopsies
        }

    def generate_weekly_markdown_artifact(self) -> str:
        """Compiles the master markdown audit document and saves to artifact directory."""
        data = self.get_weekly_report(days=7)
        now_str = datetime.now(IST).strftime("%d-%b-%Y %I:%M %p IST")

        md = f"""# 📊 HERMES 3.5 DUAL-TIER SNIPER: 7-DAY ROLLING AUDIT & FORENSIC TRACKER
**Active Strategy**: `{data['strategy']}`  
**Audit Period**: Rolling 7 Days (Updated: `{now_str}`)  
**Universe**: Top-28 Institutional Champions (22 Core + 6 Golden Additions)  
**Execution Sizing**: 100% Compounding Margin Queue | 5x Isolated Leverage  

---

## 🏆 1. Weekly Master Performance Summary

| Metric | Weekly Value | Status / Benchmark |
| :--- | :--- | :--- |
| **Total Trades Executed** | **{data['total_trades']} trades** | 24/7 Live Automated Queue |
| **Weekly Win Rate %** | **{data['win_rate']}%** ({data['wins']}W / {data['losses']}L) | Target Benchmark: $\ge 85.0\%$ |
| **LONG Accuracy** | **{data['long_metrics']['win_rate']}%** ({data['long_metrics']['wins']}W / {data['long_metrics']['losses']}L) | 15m Micro-Sniper Rejection Gate |
| **SHORT Accuracy** | **{data['short_metrics']['win_rate']}%** ({data['short_metrics']['wins']}W / {data['short_metrics']['losses']}L) | Runaway Rocket Protection Gate |
| **Gross Profit / Loss** | **+${data.get('gross_profit_usdt', 0.0):.2f} / -${data.get('gross_loss_usdt', 0.0):.2f}** | Profit Factor: **{data.get('profit_factor', 0.0)}** |
| **Net Realized PnL** | **${data['net_pnl_usdt']:+.2f} USDT** | Net After Exchange Fees |
| **Average MAE (Max Drawdown)** | **{data['avg_mae_pct']:.2f}% ROE** | Tightly Contained Risk Buffer |
| **Average MFE (Peak Profit)** | **{data['avg_mfe_pct']:.2f}% ROE** | Multi-Stage Profit Armor Capture |
| **Total Portfolio Equity** | **${data['total_portfolio_equity']:,.2f} USDT** | Compounding + Vault Stash |
| **Currently Active Trades** | **{data['open_positions_count']} positions** | Live Market Monitoring |

---

## 📍 2. Current Active Positions ({data['open_positions_count']})

| # | Coin | Side | Timeframe | Entry Price | TP Target | Stop Loss | Margin (USDT) | Sentry / Strategy Mode |
| :- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
"""
        if data['open_positions']:
            for p in data['open_positions']:
                s_reasons = (p.get('sentry_reasons') or 'Hermes 3.5 Dual-Tier')[:45]
                md += f"| #{p['id']} | **{p['symbol']}** | `{p['side']}` | {p.get('timeframe','4h').upper()} | `${float(p.get('entry_price',0)):.4f}` | `${float(p.get('tp_price',0)):.4f}` | `${float(p.get('sl_price',0)):.4f}` | `${float(p.get('position_size_usdt',250))/5.0:.2f}` | {s_reasons} |\n"
        else:
            md += "| - | *No open trades* | - | - | - | - | - | - | *Scanning Top-28 Champions for 1st Tap...* |\n"

        md += f"""
---

## 📜 3. Closed Trades History (Last 7 Days)

| # | Coin | Side | TF | Entry Price | Exit Price | PnL (USDT) | ROE % | MAE % | MFE % | Duration | Outcome |
| :- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
"""
        if data['closed_trades']:
            for t in data['closed_trades'][-20:]:  # Last 20 closed trades
                pnl = float(t.get('pnl_usdt') or 0.0)
                pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
                roe = float(t.get('roi_pct') or t.get('pnl_pct') or 0.0)
                roe_str = f"+{roe:.2f}%" if roe >= 0 else f"{roe:.2f}%"
                mae = float(t.get('mae_pct') or 0.0)
                mfe = float(t.get('mfe_pct') or 0.0)
                dur = str(t.get('duration_str') or 'N/A')
                status = str(t.get('status') or 'CLOSED')
                md += f"| #{t['id']} | **{t['symbol']}** | `{t['side']}` | {str(t.get('timeframe','4h')).upper()} | `${float(t.get('entry_price',0)):.4f}` | `${float(t.get('exit_price',0)):.4f}` | `{pnl_str}` | `{roe_str}` | `{mae:.1f}%` | `{mfe:.1f}%` | {dur} | **{status}** |\n"
        else:
            md += "| - | *No closed trades yet in this cycle* | - | - | - | - | - | - | - | - | - | - |\n"

        md += f"""
---

## 🩺 4. Loss Forensic Autopsy Matrix (Kyu SL Hit Hua?)

> [!NOTE]
> Har loss ka systematic post-mortem hota hai taaki pata chale ki Stop Loss kyu hit hua (BTC causal pressure, pre-TP runner reversal, liquidation wick, ya standard structural failure).

| Trade # | Symbol | Side | PnL | MAE / MFE | Root Cause Category | Detailed Autopsy Diagnosis |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
"""
        if data['autopsies']:
            for a in data['autopsies']:
                mae_mfe = f"-{float(a.get('mae_pct',0)):.1f}% / +{float(a.get('mfe_pct',0)):.1f}%"
                cat = a.get('loss_category', 'STRUCTURAL_STOP')
                diag = a.get('autopsy_diagnosis', 'Standard structural stop')
                pnl = float(a.get('pnl_usdt', 0.0))
                md += f"| #{a.get('trade_id','-')} | **{a['symbol']}** | `{a['side']}` | `-${abs(pnl):.2f}` | `{mae_mfe}` | **{cat}** | {diag} |\n"
        else:
            md += "| - | *Zero Stop Losses recorded in this audit cycle!* | - | - | - | - | *100% Capital Integrity Preserved.* |\n"

        md += """
---

## 🛡️ 5. Next Steps & Continuous Monitoring Protocol

1. **Daily Auto-Audit**: Har raat 12:00 baje IST system daily snapshot record karta hai.
2. **Weekly Performance Check**: Har 7 din baad user ko master accuracy, win rate, MAE/MFE aur autopsy report pesh ki jaati hai.
3. **Autonomous AI Doctor Active**: Agar koi trade apne stop loss ya 48h limit ko breach karega, toh Sentinel use bina ruke auto-close karega aur root cause log karega.
"""

        # Save to Artifacts directory
        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        art_file = os.path.join(ARTIFACT_DIR, "HERMES_3.5_7DAY_LIVE_MONITOR_TRACKER.md")
        try:
            with open(art_file, "w", encoding="utf-8") as f:
                f.write(md)
            logger.info(f"💾 Updated artifact: {art_file}")
        except Exception as e:
            logger.error(f"Failed to write artifact: {e}")

        return art_file


weekly_monitor = Hermes35WeeklyMonitor()
