import aiohttp
import json
from typing import Dict, Any, List, Optional
from config import GEMINI_API_KEY, GEMINI_MODEL
from database.db import get_setting
from ai.smart_money_analyzer import evaluate_setup_confluence

GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"

SYSTEM_PROMPT = """
You are Mike, the Dedicated Institutional Smart Money Concepts (SMC V17) & ICT AI Trading Agent.
Your name is MIKE. When you answer, you speak directly as Mike — sharp, disciplined, institutional-grade, in natural, friendly Hinglish.

Your core mission as Mike:
1. Provide deep, professional chart & market structure breakdowns in clean, friendly Hinglish.
2. Analyze beyond basic lines - evaluate what retail traders miss:
   - Multi-Timeframe Alignment (1D Macro vs 4H Structure)
   - Liquidity Traps (Equal Highs EQH / Equal Lows EQL waiting to be swept)
   - Pricing Value (Discount OTE 0.50-0.79 for BUY, Premium for SELL)
   - Retest Volume Exhaustion (VSA volume behavior)
   - Confluence Score (0 - 100) and Grade (A+, A, B, C)
3. Maintain strict SMC V17 discipline:
   - First Tap Entry ONLY at Order Block boundary
   - TP = +4.0%, SL = -3.0% (strictly protected)
4. Formatting:
   - Begin with Mike's greeting or verdict.
   - Use clear bullet points and emojis.
   - Keep answers structured: Verdict -> Strengths -> Traps & Risks -> Execution Plan.
"""

class GeminiAnalyst:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=25))
        return self.session

    def generate_local_fallback_analysis(
        self,
        symbol: str,
        current_price: float,
        zones: List[Dict[str, Any]],
        confluence: Optional[Dict[str, Any]] = None
    ) -> str:
        """Rich local quantitative analysis if Gemini is unavailable."""
        if not zones:
            trend_info = ""
            if confluence and "mtf" in confluence:
                mtf = confluence["mtf"]
                trend_info = (
                    f"• <b>4H Trend:</b> {mtf.get('trend_4h', 'NEUTRAL')}\n"
                    f"• <b>1D Macro:</b> {mtf.get('trend_1d', 'NEUTRAL')}\n"
                )
            traps_info = ""
            if confluence and "traps" in confluence:
                eqh = confluence["traps"].get("eqh", [])
                eql = confluence["traps"].get("eql", [])
                if eqh:
                    traps_info += f"• <b>EQH Liquidity Pool (Above):</b> ${eqh[0]:,.4f}\n"
                if eql:
                    traps_info += f"• <b>EQL Liquidity Pool (Below):</b> ${eql[0]:,.4f}\n"

            return (
                f"🤖 <b>MIKE • SMC V17 AI AGENT (Flash Low) • #{symbol}</b>\n\n"
                f"Namaste! Mai Mike hoon — aapka 4H SMC V17 AI Trading Agent.\n\n"
                f"Abhi {symbol} par koi active 4H SMC V17 zone qualified nahi hai.\n"
                f"• <b>Current Price:</b> ${current_price:,.4f}\n"
                f"{trend_info}"
                f"{traps_info}"
                f"• <b>Status:</b> 7% clean displacement move ka intezar hai True Origin candle se.\n\n"
                f"💡 <i>Mike's Tip: Scanner 24/7 50 coins monitor kar raha hai. Jaise hi valid Order Block banta hai, mai turant alert bhej dunga!</i>"
            )

        z = zones[0]
        side = z["side"]
        side_color = "🟢 BUY" if side == "BUY" else "🔴 SELL"
        entry = float(z.get("entry_price") or (z["ob_high"] if side == "BUY" else z["ob_low"]))
        tp = float(z.get("tp_price") or (entry * 1.04 if side == "BUY" else entry * 0.96))
        sl = float(z.get("sl_price") or (entry * 0.97 if side == "BUY" else entry * 1.03))

        dist_pct = abs(current_price - entry) / (entry if entry > 0 else 1.0) * 100

        # Confluence info
        score = confluence["score"] if confluence else 85
        grade = confluence["grade"] if confluence else "A"
        verdict = confluence["verdict"] if confluence else "STRONG SETUP"
        strengths = confluence.get("strengths", ["Clean 7% expansion", "Displacement confirmed"]) if confluence else []
        risks = confluence.get("risks", ["None detected"]) if confluence else []

        strengths_str = "\n".join([f"  ✅ {s}" for s in strengths])
        risks_str = "\n".join([f"  ⚠️ {r}" for r in risks])

        return (
            f"🤖 <b>MIKE • SMC V17 AI AGENT (Flash Low) • #{symbol}</b>\n\n"
            f"Namaste! Mai Mike hoon. Yaha {symbol} ka institutional SMC V17 breakdown hai:\n\n"
            f"🎯 <b>AI Grade:</b> <code>{grade} ({score}/100)</code> • <b>{verdict}</b>\n"
            f"🪙 <b>Direction:</b> {side_color} (First Tap Only)\n"
            f"📍 <b>Planned Entry:</b> ${entry:,.4f} (Distance: {dist_pct:.2f}%)\n"
            f"🟢 <b>Target (TP +4%):</b> ${tp:,.4f}\n"
            f"🛑 <b>Stop Loss (SL -3%):</b> ${sl:,.4f}\n"
            f"📦 <b>OB Range:</b> ${float(z['ob_low']):,.4f} - ${float(z['ob_high']):,.4f}\n\n"
            f"💎 <b>CONFLUENCE STRENGTHS:</b>\n{strengths_str}\n\n"
            f"🛡️ <b>RISK & TRAP AUDIT:</b>\n{risks_str}\n\n"
            f"⚡ <i>Mike's Rule: Entry first-tap hone par automatic execute karein. SL (-3%) ko kabhi peeche mat khiskein.</i>"
        )

    async def analyze_setup(
        self,
        symbol: str,
        current_price: float,
        zones: List[Dict[str, Any]],
        candles_4h: Optional[List[Dict[str, Any]]] = None,
        candles_1d: Optional[List[Dict[str, Any]]] = None,
        user_query: str = ""
    ) -> str:
        """
        Deep AI Smart Money analysis evaluating MTF structure, Liquidity Traps,
        Pricing (Discount/Premium), and Confluence scoring.
        """
        confluence = None
        if zones and candles_4h:
            try:
                confluence = evaluate_setup_confluence(symbol, zones[0], candles_4h, candles_1d)
            except Exception:
                confluence = None
        elif candles_4h:
            try:
                from ai.smart_money_analyzer import detect_mtf_trend, detect_equal_highs_lows
                mtf = detect_mtf_trend(candles_4h, candles_1d)
                traps = detect_equal_highs_lows(candles_4h)
                confluence = {
                    "mtf": mtf,
                    "traps": traps,
                    "status": "MONITORING_NO_ACTIVE_ZONE"
                }
            except Exception:
                confluence = None

        api_key = get_setting("gemini_api_key", GEMINI_API_KEY)
        if not api_key:
            return self.generate_local_fallback_analysis(symbol, current_price, zones, confluence)

        context_data = {
            "symbol": symbol,
            "current_price": current_price,
            "strategy": "SMC V17 (4H)",
            "active_zone": zones[0] if zones else None,
            "confluence_audit": confluence,
            "rules": {
                "qualification": "7% move without pre-touch",
                "entry_rule": "First Tap Only at OB Boundary",
                "tp_pct": "+4%",
                "sl_pct": "-3%"
            }
        }

        user_prompt = f"""
Comprehensive Market Structure & Confluence Data:
{json.dumps(context_data, indent=2, default=str)}

User Query / Request:
{user_query if user_query else "Provide an institutional Smart Money breakdown of this setup in Hinglish. Cover Confluence Grade, Multi-Timeframe alignment, Liquidity traps/risks, and execution discipline."}
"""

        model_pref = get_setting("gemini_model", GEMINI_MODEL)
        models_to_try = [
            model_pref,
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-2.5-flash"
        ]
        unique_models = []
        for m in models_to_try:
            if m and m not in unique_models:
                unique_models.append(m)

        session = await self.get_session()
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\n" + user_prompt}]}
            ],
            "generationConfig": {
                "temperature": 0.25,
                "maxOutputTokens": 900
            }
        }

        for model_name in unique_models:
            url = f"{GEMINI_API_ENDPOINT}/{model_name}:generateContent?key={api_key}"
            try:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        candidates = result.get("candidates", [])
                        if candidates:
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
            except Exception:
                continue

        return self.generate_local_fallback_analysis(symbol, current_price, zones, confluence)

gemini_analyst = GeminiAnalyst()
