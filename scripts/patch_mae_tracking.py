import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 1. Patch scripts/run_bb20_live_sniper.py
bb_sniper_path = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\scripts\run_bb20_live_sniper.py"
with open(bb_sniper_path, "r", encoding="utf-8") as f:
    content = f.read()

old_bb = """        if side == "LONG":
            fav_spot_gain = (high_price - entry) / entry
        else:
            fav_spot_gain = (entry - low_price) / entry

        curr_peak_roi = round(fav_spot_gain * leverage * 100.0, 2)
        if curr_peak_roi > pos.get("peak_roi", 0.0):
            pos["peak_roi"] = curr_peak_roi

        # 3. Continuous Stepped Trailing SL Check
        tier_candidate = get_roi_trailing_tier(curr_peak_roi)
        if tier_candidate > current_tier:
            pos["current_tier"] = tier_candidate
            locked_roi = get_locked_roi(tier_candidate)
            new_sl = calculate_trailing_sl_price(entry, side, locked_roi, leverage)
            pos["active_sl"] = round(new_sl, 4)
            pos["locked_roi"] = locked_roi

            _sync_to_nexuspro_render("TRAILING", {
                "symbol": symbol,
                "trailing_sl": new_sl,
                "stage": tier_candidate,
                "locked_roi": locked_roi,
                "peak_roi": curr_peak_roi
            })"""

new_bb = """        if side == "LONG":
            fav_spot_gain = (high_price - entry) / entry
            adv_spot_loss = (entry - low_price) / entry if low_price < entry else 0.0
        else:
            fav_spot_gain = (entry - low_price) / entry
            adv_spot_loss = (high_price - entry) / entry if high_price > entry else 0.0

        curr_peak_roi = round(fav_spot_gain * leverage * 100.0, 2)
        curr_mae_roi = round(adv_spot_loss * leverage * 100.0, 2)

        if curr_peak_roi > pos.get("peak_roi", 0.0):
            pos["peak_roi"] = curr_peak_roi
            pos["mfe_pct"] = curr_peak_roi

        if curr_mae_roi > pos.get("mae_pct", 0.0):
            pos["mae_pct"] = curr_mae_roi

        # 3. Continuous Stepped Trailing SL Check
        tier_candidate = get_roi_trailing_tier(curr_peak_roi)
        if tier_candidate > current_tier:
            pos["current_tier"] = tier_candidate
            locked_roi = get_locked_roi(tier_candidate)
            new_sl = calculate_trailing_sl_price(entry, side, locked_roi, leverage)
            pos["active_sl"] = round(new_sl, 4)
            pos["locked_roi"] = locked_roi

            _sync_to_nexuspro_render("TRAILING", {
                "symbol": symbol,
                "trailing_sl": new_sl,
                "stage": tier_candidate,
                "locked_roi": locked_roi,
                "peak_roi": curr_peak_roi,
                "mfe_pct": curr_peak_roi,
                "mae_pct": pos.get("mae_pct", 0.0)
            })"""

old_bb_crlf = old_bb.replace("\r\n", "\n").replace("\n", "\r\n")
new_bb_crlf = new_bb.replace("\r\n", "\n").replace("\n", "\r\n")

if old_bb_crlf in content:
    content = content.replace(old_bb_crlf, new_bb_crlf)
    with open(bb_sniper_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Successfully patched scripts/run_bb20_live_sniper.py")
elif old_bb in content:
    content = content.replace(old_bb, new_bb)
    with open(bb_sniper_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Successfully patched scripts/run_bb20_live_sniper.py (LF)")
else:
    print("⚠️ Could not find target in run_bb20_live_sniper.py")

# 2. Patch static/mobile.html
mobile_path = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\static\mobile.html"
with open(mobile_path, "r", encoding="utf-8") as f:
    mob_content = f.read()

old_mob = """                                    <!-- MAE & MFE Live Data Injection -->
                                    <div class="bpc-cell" style="background:rgba(255, 77, 106, 0.08); padding:5px 7px; border-radius:6px; border:1px solid rgba(255, 77, 106, 0.2);">
                                        <span class="bpc-cell-label" style="color:var(--red); font-weight:800;">MAE (Drawdown)</span>
                                        <span class="bpc-cell-val" style="color:var(--red); font-weight:900;">-${Number(p.mae_pct || 0).toFixed(2)}%</span>
                                    </div>
                                    <div class="bpc-cell" style="background:rgba(0, 245, 155, 0.08); padding:5px 7px; border-radius:6px; border:1px solid rgba(0, 245, 155, 0.2);">
                                        <span class="bpc-cell-label" style="color:var(--green); font-weight:800;">MFE (Peak Profit)</span>
                                        <span class="bpc-cell-val" style="color:var(--green); font-weight:900;">+${Number(p.mfe_pct || 0).toFixed(2)}%</span>
                                    </div>"""

new_mob = """                                    <!-- MAE & MFE Live Data Injection -->
                                    <div class="bpc-cell" style="background:rgba(255, 77, 106, 0.08); padding:5px 7px; border-radius:6px; border:1px solid rgba(255, 77, 106, 0.2);">
                                        <span class="bpc-cell-label" style="color:var(--red); font-weight:800;">MAE (Drawdown)</span>
                                        <span class="bpc-cell-val" style="color:var(--red); font-weight:900;">-${Math.max(Number(p.mae_pct || 0), pnl < 0 ? Math.abs(Number(p.pnl_pct || 0)) : 0).toFixed(2)}%</span>
                                    </div>
                                    <div class="bpc-cell" style="background:rgba(0, 245, 155, 0.08); padding:5px 7px; border-radius:6px; border:1px solid rgba(0, 245, 155, 0.2);">
                                        <span class="bpc-cell-label" style="color:var(--green); font-weight:800;">MFE (Peak Profit)</span>
                                        <span class="bpc-cell-val" style="color:var(--green); font-weight:900;">+${Math.max(Number(p.mfe_pct || 0), Math.max(0, Number(p.pnl_pct || 0))).toFixed(2)}%</span>
                                    </div>"""

old_mob_crlf = old_mob.replace("\r\n", "\n").replace("\n", "\r\n")
new_mob_crlf = new_mob.replace("\r\n", "\n").replace("\n", "\r\n")

if old_mob_crlf in mob_content:
    mob_content = mob_content.replace(old_mob_crlf, new_mob_crlf)
    with open(mobile_path, "w", encoding="utf-8") as f:
        f.write(mob_content)
    print("✅ Successfully patched static/mobile.html")
elif old_mob in mob_content:
    mob_content = mob_content.replace(old_mob, new_mob)
    with open(mobile_path, "w", encoding="utf-8") as f:
        f.write(mob_content)
    print("✅ Successfully patched static/mobile.html (LF)")
else:
    print("⚠️ Could not find target in static/mobile.html")

# 3. Patch app.py in smc_v17_trading_system
app_path = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\app.py"
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

old_app = """        if is_buy:
            live_mfe = round(max(0.0, (highest_p - entry) / entry * 100.0 * leverage), 2)
            live_mae = round(max(0.0, (entry - lowest_p) / entry * 100.0 * leverage), 2)
        else:
            live_mfe = round(max(0.0, (entry - lowest_p) / entry * 100.0 * leverage), 2)
            live_mae = round(max(0.0, (highest_p - entry) / entry * 100.0 * leverage), 2)"""

new_app = """        if is_buy:
            live_mfe = round(max(0.0, (highest_p - entry) / entry * 100.0 * leverage), 2)
            live_mae = round(max(0.0, (entry - lowest_p) / entry * 100.0 * leverage), 2)
        else:
            live_mfe = round(max(0.0, (entry - lowest_p) / entry * 100.0 * leverage), 2)
            live_mae = round(max(0.0, (highest_p - entry) / entry * 100.0 * leverage), 2)

        # Dynamic Guarantee: MAE must always reflect at least the current drawdown if negative, MFE if positive
        if roi_pct < 0:
            live_mae = max(live_mae, round(abs(roi_pct), 2))
        else:
            live_mfe = max(live_mfe, round(roi_pct, 2))"""

old_app_crlf = old_app.replace("\r\n", "\n").replace("\n", "\r\n")
new_app_crlf = new_app.replace("\r\n", "\n").replace("\n", "\r\n")

if old_app_crlf in app_content:
    app_content = app_content.replace(old_app_crlf, new_app_crlf)
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_content)
    print("✅ Successfully patched app.py in smc_v17_trading_system")
elif old_app in app_content:
    app_content = app_content.replace(old_app, new_app)
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_content)
    print("✅ Successfully patched app.py in smc_v17_trading_system (LF)")
else:
    print("⚠️ Could not find target in app.py")
