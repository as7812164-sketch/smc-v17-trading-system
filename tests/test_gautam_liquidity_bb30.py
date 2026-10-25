import os
import sys
import unittest
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import bb20_config as cfg
from scripts.run_bb20_live_sniper import get_session_killzone, BB20LiveSniper
from engine.bb_model3_engine import BBModel3Engine, get_session_killzone as eng_get_session_killzone

class TestGautamInstitutionalLiquidity(unittest.TestCase):
    def test_bb20_config_constants(self):
        self.assertEqual(cfg.TARGET_MODE, "OPPOSITE_DAILY_LIQUIDITY")
        self.assertEqual(cfg.MIN_RR_RATIO, 2.5)
        self.assertTrue(cfg.ENABLE_KILLZONE_PRIORITY)
        self.assertEqual(cfg.PARTIAL_TP_LOCK_PCT, 0.90)
        self.assertEqual(cfg.TIME_PASS_EXHAUSTION_PCT, 0.85)

    def test_session_killzones(self):
        # 08:00 UTC -> London Killzone (covers Gautam 2:00 PM IST Trap)
        dt_london = datetime(2026, 10, 24, 8, 30, tzinfo=timezone.utc).timestamp() * 1000
        self.assertEqual(get_session_killzone(dt_london), "London Killzone")
        self.assertEqual(eng_get_session_killzone(dt_london), "London Killzone")

        # 14:00 UTC -> NY Killzone
        dt_ny = datetime(2026, 10, 24, 14, 30, tzinfo=timezone.utc).timestamp() * 1000
        self.assertEqual(get_session_killzone(dt_ny), "NY Killzone")
        self.assertEqual(eng_get_session_killzone(dt_ny), "NY Killzone")

        # 03:00 UTC -> Asian Session
        dt_asia = datetime(2026, 10, 24, 3, 0, tzinfo=timezone.utc).timestamp() * 1000
        self.assertEqual(get_session_killzone(dt_asia), "Asian Session")
        self.assertEqual(eng_get_session_killzone(dt_asia), "Asian Session")

        # 20:00 UTC -> Off-Hours
        dt_off = datetime(2026, 10, 24, 20, 0, tzinfo=timezone.utc).timestamp() * 1000
        self.assertEqual(get_session_killzone(dt_off), "Off-Hours")
        self.assertEqual(eng_get_session_killzone(dt_off), "Off-Hours")

    def test_bb_model3_engine_opposite_liquidity_tagging(self):
        engine = BBModel3Engine()
        pdh = 100.0
        pdl = 90.0

        # Create mock 15m candles near PDL (at least 4 candles for i=1 to evaluate)
        ts = datetime(2026, 10, 24, 8, 0, tzinfo=timezone.utc).timestamp() * 1000
        candles = [
            {"time": ts - 900000, "open": 91.0, "high": 91.5, "low": 90.5, "close": 90.8, "volume": 1000},
            {"time": ts, "open": 90.5, "high": 91.0, "low": 89.8, "close": 90.1, "volume": 1000}, # OB at PDL
            {"time": ts + 900000, "open": 90.1, "high": 93.0, "low": 90.0, "close": 92.8, "volume": 2000}, # Displacement (>1.5%)
            {"time": ts + 1800000, "open": 92.8, "high": 94.0, "low": 91.5, "close": 93.5, "volume": 1500}, # FVG: low 91.5 > high 91.0
        ]

        obs = engine.find_extreme_order_blocks(candles, pdh, pdl)
        self.assertTrue(len(obs) > 0)
        ob = obs[0]
        self.assertEqual(ob["side"], "LONG")
        self.assertEqual(ob["opposite_liquidity"], pdh)
        self.assertGreaterEqual(ob["target_rr"], 2.5)
        self.assertEqual(ob["killzone"], "London Killzone")
        self.assertEqual(ob["liquidity_source"], "-1 Day Liquidity (PDL/PDH Sweep)")

    def test_opposite_liquidity_partial_lock_and_moonbag(self):
        engine = BBModel3Engine()
        entry = 90.0
        sl = 88.0
        risk = 2.0
        target_price = 100.0 # 5R
        target_rr = 5.0

        setup = {
            "side": "LONG",
            "index": 0,
            "mt": entry,
            "sl": sl,
            "risk": risk,
            "target_price": target_price,
            "target_rr": target_rr,
            "opposite_liquidity": target_price,
            "killzone": "London Killzone"
        }

        # Candles where price fills, touches target (100.0), and then drops to active_sl
        candles = [
            {"high": 91.0, "low": 90.2}, # bar 0
            {"high": 91.0, "low": 90.2}, # bar 1
            {"high": 90.5, "low": 89.5}, # bar 2 (fill at 90.0)
            {"high": 100.5, "low": 91.0}, # bar 3 (touches target 100.0 -> 90% lock, SL moved to 94.0 = +2.0R)
            {"high": 95.0, "low": 93.5},  # bar 4 (hits active_sl at 94.0)
        ]

        res = engine.check_active_setup_state(setup, candles)
        self.assertEqual(res["state"], "CLOSED")
        self.assertEqual(res["outcome"], "OPPOSITE_LIQUIDITY_90PCT_LOCK")
        self.assertTrue(res["partial_90_taken"])
        # Expected pnl_r: (5.0 * 0.90) + (2.0 * 0.10) - 0.06 = 4.5 + 0.2 - 0.06 = 4.64R
        self.assertAlmostEqual(res["pnl_r"], 4.64, places=2)

if __name__ == "__main__":
    unittest.main()
