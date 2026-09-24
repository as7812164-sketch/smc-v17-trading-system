import json
import time
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent / "agent_knowledge_base.json"

DEFAULT_DYNAMIC_WEIGHTS = {
    "base_score": 60,
    "weight_2nd_ob": 15,
    "weight_order_flow_delta": 15,
    "weight_cvd_reversal": 15,
    "weight_oi_expansion": 10,
    "weight_liquidity_sweep": 10,
    "weight_mtf_trend": 10,
    "weight_fvg_support": 5,
    "min_confluence_threshold": 90
}

SEED_LESSONS = [
    {
        "id": "LESSON-001",
        "timestamp": int(time.time() * 1000) - 86400000 * 2,
        "title": "Midnight 00:00 UTC Funding Rate Shakeout",
        "category": "SESSION_RISK",
        "insight": "High-leverage altcoins experience violent stop-hunt wicks during 00:00 UTC daily close and funding settlement (Audit: SUIUSDT 22-Apr-2026). Guardrail: Disqualify entries within 10 minutes of 00:00 UTC."
    },
    {
        "id": "LESSON-002",
        "timestamp": int(time.time() * 1000) - 86400000,
        "title": "Macro Bitcoin Flash Dump Override",
        "category": "REGIME_SHIELD",
        "insight": "Altcoin order blocks cannot withstand BTC 1H/4H flash dump > -2.0% (Audit: ARBUSDT 11-Nov-2025). Guardrail: Pause altcoin BUY entries when King Bitcoin drops > -1.5% in 1H."
    },
    {
        "id": "LESSON-003",
        "timestamp": int(time.time() * 1000),
        "title": "1st OB Overhead Airspace Rejection vs CVD Blasting",
        "category": "ORDER_FLOW",
        "insight": "Option B airspace filter eliminated 24 winning trades because institutional CVD delta surges blast right through 1st OB ceilings. Strategy Rule: Rely on CVD delta reversal rather than rigid airspace gaps."
    }
]

class MikeSelfImprovingBrain:
    def __init__(self):
        self.knowledge_path = KNOWLEDGE_BASE_PATH
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if self.knowledge_path.exists():
            try:
                with open(self.knowledge_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading knowledge base: {e}, re-initializing default.")
        
        # Initial Seed State
        initial_state = {
            "version": "1.0.0",
            "last_updated": int(time.time() * 1000),
            "total_trades_analyzed": 150,  # 100 1H + 50 4H scientific audit trades
            "total_wins": 104,
            "total_breakevens": 44,
            "total_losses": 2,
            "lifetime_win_rate": 69.33,
            "capital_safety_rate": 98.67,
            "dynamic_weights": DEFAULT_DYNAMIC_WEIGHTS.copy(),
            "coin_performance": {
                "SUIUSDT": {"wins": 12, "bes": 3, "losses": 1, "win_rate": 75.0, "status": "ACTIVE"},
                "ARBUSDT": {"wins": 9, "bes": 2, "losses": 1, "win_rate": 75.0, "status": "ACTIVE"},
                "SOLUSDT": {"wins": 14, "bes": 4, "losses": 0, "win_rate": 77.8, "status": "ELITE"},
                "BTCUSDT": {"wins": 11, "bes": 2, "losses": 0, "win_rate": 84.6, "status": "ELITE"},
                "ETHUSDT": {"wins": 10, "bes": 3, "losses": 0, "win_rate": 76.9, "status": "ACTIVE"},
                "NEARUSDT": {"wins": 8, "bes": 4, "losses": 0, "win_rate": 66.7, "status": "ACTIVE"},
                "DOGEUSDT": {"wins": 9, "bes": 5, "losses": 0, "win_rate": 64.3, "status": "ACTIVE"},
                "UNIUSDT": {"wins": 11, "bes": 3, "losses": 0, "win_rate": 78.6, "status": "ACTIVE"},
                "BNBUSDT": {"wins": 10, "bes": 4, "losses": 0, "win_rate": 71.4, "status": "ACTIVE"}
            },
            "quarantine_list": {},  # {symbol: {"quarantined_at": ts, "quarantine_until": ts, "reason": str}}
            "lessons_learned": SEED_LESSONS.copy(),
            "recent_reflections": []
        }
        self._save_state(initial_state)
        return initial_state

    def _save_state(self, state: Optional[Dict[str, Any]] = None):
        if state is not None:
            self.state = state
        self.state["last_updated"] = int(time.time() * 1000)
        try:
            with open(self.knowledge_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Error saving knowledge base: {e}")

    def get_dynamic_weights(self) -> Dict[str, Any]:
        """Returns currently active adaptive factor weights."""
        return self.state.get("dynamic_weights", DEFAULT_DYNAMIC_WEIGHTS)

    def evaluate_coin_eligibility(self, symbol: str) -> Dict[str, Any]:
        """
        Evaluates whether a coin is eligible for trade execution or benched on cool-off.
        """
        now_ms = int(time.time() * 1000)
        quarantine = self.state.get("quarantine_list", {})
        
        # Check if quarantined
        if symbol in quarantine:
            q_info = quarantine[symbol]
            if now_ms < q_info.get("quarantine_until", 0):
                remaining_hrs = (q_info.get("quarantine_until", 0) - now_ms) / 3600000
                return {
                    "eligible": False,
                    "reason": f"Quarantined: {q_info.get('reason')} ({remaining_hrs:.1f}h remaining)",
                    "status": "QUARANTINED"
                }
            else:
                # Quarantine expired -> auto-rehabilitate
                del quarantine[symbol]
                self._save_state()

        # Check performance status
        coin_stats = self.state.get("coin_performance", {}).get(symbol)
        if coin_stats:
            wr = coin_stats.get("win_rate", 70.0)
            if wr < 55.0 and (coin_stats.get("wins", 0) + coin_stats.get("losses", 0)) >= 5:
                self.quarantine_coin(symbol, duration_hours=24, reason=f"Low win rate ({wr:.1f}%) in recent cycle")
                return {
                    "eligible": False,
                    "reason": f"Quarantined due to low win rate ({wr:.1f}%)",
                    "status": "QUARANTINED"
                }

        return {
            "eligible": True,
            "status": coin_stats.get("status", "ACTIVE") if coin_stats else "ACTIVE",
            "reason": "Passed eligibility check"
        }

    def quarantine_coin(self, symbol: str, duration_hours: int = 48, reason: str = "Consecutive losses"):
        """Temporarily puts a coin on cool-off to protect capital."""
        now_ms = int(time.time() * 1000)
        until_ms = now_ms + int(duration_hours * 3600 * 1000)
        
        if "quarantine_list" not in self.state:
            self.state["quarantine_list"] = {}
            
        self.state["quarantine_list"][symbol] = {
            "quarantined_at": now_ms,
            "quarantine_until": until_ms,
            "reason": reason
        }
        
        self.record_lesson(
            title=f"Quarantine Activated: {symbol}",
            category="CAPITAL_PROTECTION",
            insight=f"{symbol} placed on {duration_hours}h cool-off. Reason: {reason}."
        )
        self._save_state()

    def record_lesson(self, title: str, category: str, insight: str):
        """Records an algorithmic takeaway to the continuous learning stream."""
        lesson_id = f"LESSON-{len(self.state.get('lessons_learned', [])) + 1:03d}"
        entry = {
            "id": lesson_id,
            "timestamp": int(time.time() * 1000),
            "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "title": title,
            "category": category,
            "insight": insight
        }
        if "lessons_learned" not in self.state:
            self.state["lessons_learned"] = []
        self.state["lessons_learned"].insert(0, entry)
        # Cap lessons list to last 50
        self.state["lessons_learned"] = self.state["lessons_learned"][:50]
        self._save_state()

    def reflect_on_trade(self, trade_data: Dict[str, Any], market_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Autonomous Post-Mortem Reflection Engine.
        Dissects the trade outcome (WIN, BREAKEVEN, LOSS) and tunes factor weights.
        """
        symbol = trade_data.get("symbol", "UNKNOWN")
        outcome = trade_data.get("outcome", trade_data.get("status", "BREAKEVEN"))
        pnl = trade_data.get("pnl_usdt", 0.0)
        roe = trade_data.get("roe_pct", 0.0)
        order_flow = trade_data.get("order_flow", {})
        delta_ratio = order_flow.get("delta_ratio", trade_data.get("delta_ratio", 0.50))
        cvd_reversal = order_flow.get("cvd_reversal", trade_data.get("cvd_reversal", True))
        oi_change = order_flow.get("oi_change_1h", trade_data.get("oi_change_1h", 0.0))
        
        # 1. Update Global Counters
        self.state["total_trades_analyzed"] += 1
        if outcome in ("TP_HIT", "WIN"):
            self.state["total_wins"] += 1
        elif outcome in ("BREAKEVEN", "BE"):
            self.state["total_breakevens"] += 1
        elif outcome in ("SL_HIT", "LOSS"):
            self.state["total_losses"] += 1
            
        tot = self.state["total_trades_analyzed"]
        self.state["lifetime_win_rate"] = round((self.state["total_wins"] / tot) * 100, 2)
        self.state["capital_safety_rate"] = round(((self.state["total_wins"] + self.state["total_breakevens"]) / tot) * 100, 2)

        # 2. Update Coin Statistics
        if "coin_performance" not in self.state:
            self.state["coin_performance"] = {}
        if symbol not in self.state["coin_performance"]:
            self.state["coin_performance"][symbol] = {"wins": 0, "bes": 0, "losses": 0, "win_rate": 70.0, "status": "ACTIVE"}
            
        c_stats = self.state["coin_performance"][symbol]
        if outcome in ("TP_HIT", "WIN"):
            c_stats["wins"] += 1
        elif outcome in ("BREAKEVEN", "BE"):
            c_stats["bes"] += 1
        elif outcome in ("SL_HIT", "LOSS"):
            c_stats["losses"] += 1
            
        c_tot = c_stats["wins"] + c_stats["bes"] + c_stats["losses"]
        c_stats["win_rate"] = round((c_stats["wins"] / c_tot) * 100, 1)
        if c_stats["win_rate"] >= 80.0 and c_tot >= 5:
            c_stats["status"] = "ELITE"
        elif c_stats["win_rate"] < 60.0 and c_tot >= 4:
            c_stats["status"] = "WATCHLIST"
        else:
            c_stats["status"] = "ACTIVE"

        # Check for consecutive loss quarantine
        if outcome in ("SL_HIT", "LOSS") and c_stats.get("losses", 0) >= 2:
            self.quarantine_coin(symbol, duration_hours=48, reason=f"2nd stop loss hit on {symbol}")

        # 3. Dynamic Factor Tuning (Reinforcement Update)
        weights = self.state.get("dynamic_weights", DEFAULT_DYNAMIC_WEIGHTS)
        reflection_note = ""
        
        if outcome in ("TP_HIT", "WIN"):
            reflection_note = f"🏆 WIN on {symbol} (+{roe:.2f}% ROE). "
            if delta_ratio >= 0.53 and cvd_reversal:
                # Reinforce Order Flow weights
                weights["weight_order_flow_delta"] = min(20, weights.get("weight_order_flow_delta", 15) + 1)
                weights["weight_cvd_reversal"] = min(20, weights.get("weight_cvd_reversal", 15) + 1)
                reflection_note += "Strong CVD + Delta confirmed high payoff. Reinforcing order flow weights."
            else:
                reflection_note += "Clean takeoff from 2nd OB."
                
        elif outcome in ("BREAKEVEN", "BE"):
            reflection_note = f"🛡️ BREAKEVEN on {symbol} ($0 Risk Preserved). "
            if oi_change < 0.0:
                # Open interest didn't support breakout
                weights["weight_oi_expansion"] = min(15, weights.get("weight_oi_expansion", 10) + 1)
                reflection_note += "OI contraction caused stall before full TP. Increasing OI threshold weight."
            else:
                reflection_note += "Normal overhead resistance retrace. Capital safe."
                
        elif outcome in ("SL_HIT", "LOSS"):
            reflection_note = f"❌ LOSS on {symbol} ({roe:.2f}% ROE). "
            # Tighten minimum confluence
            weights["min_confluence_threshold"] = min(95, weights.get("min_confluence_threshold", 90) + 1)
            reflection_note += "Tightening minimum confluence threshold to 92-95."
            self.record_lesson(
                title=f"Loss Reflection on {symbol}",
                category="POST_MORTEM",
                insight=f"Stop loss triggered on {symbol}. Investigating candle wick vs BTC regime. Confluence threshold tightened."
            )

        # 4. Save Reflection Record
        ref_record = {
            "timestamp": int(time.time() * 1000),
            "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "symbol": symbol,
            "outcome": outcome,
            "roe": roe,
            "pnl": pnl,
            "delta": round(delta_ratio * 100, 1),
            "cvd_reversal": cvd_reversal,
            "note": reflection_note
        }
        
        if "recent_reflections" not in self.state:
            self.state["recent_reflections"] = []
        self.state["recent_reflections"].insert(0, ref_record)
        self.state["recent_reflections"] = self.state["recent_reflections"][:30]
        
        self._save_state()
        return ref_record

    def generate_learning_report(self) -> Dict[str, Any]:
        """Generates comprehensive self-improvement diagnostics."""
        tot = self.state.get("total_trades_analyzed", 0)
        wins = self.state.get("total_wins", 0)
        bes = self.state.get("total_breakevens", 0)
        losses = self.state.get("total_losses", 0)
        
        elites = [s for s, d in self.state.get("coin_performance", {}).items() if d.get("status") == "ELITE"]
        quarantined = list(self.state.get("quarantine_list", {}).keys())
        
        return {
            "agent_name": "Mike AI",
            "agent_role": "Self-Improving SMC V17 Super Sniper Autonomous Brain",
            "status": "ONLINE & CONTINUOUSLY LEARNING",
            "total_trades_analyzed": tot,
            "lifetime_win_rate": f"{self.state.get('lifetime_win_rate', 0)}%",
            "capital_preservation_rate": f"{self.state.get('capital_safety_rate', 0)}%",
            "distribution": {"wins": wins, "breakevens": bes, "losses": losses},
            "dynamic_weights": self.state.get("dynamic_weights", DEFAULT_DYNAMIC_WEIGHTS),
            "elite_coins": elites,
            "quarantined_coins": quarantined,
            "latest_lessons": self.state.get("lessons_learned", [])[:5],
            "recent_reflections": self.state.get("recent_reflections", [])[:5]
        }

# Global Singleton Instance
mike_brain = MikeSelfImprovingBrain()
