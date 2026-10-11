import io
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
from config import get_ist_now

def render_smc_chart_image(
    symbol: str,
    candles: List[Dict[str, Any]],
    zone: Dict[str, Any],
    zones: Optional[List[Dict[str, Any]]] = None,
    timeframe: str = "4H"
) -> bytes:
    """
    Renders a high-resolution, dark-themed TradingView style candlestick chart
    with Order Block zone(s), Entry, TP (+4%), SL (-3%) lines and price badges.
    Returns in-memory PNG bytes.
    """
    width = 920
    height = 540
    img = Image.new("RGBA", (width, height), color=(14, 17, 24, 255))
    draw = ImageDraw.Draw(img)

    # Use default bitmap font (guaranteed to work in any headless Linux/Windows environment)
    font = ImageFont.load_default()

    # Select last 45 candles for clean viewing
    display_candles = candles[-45:] if len(candles) > 45 else candles
    if not display_candles:
        # Fallback empty image
        draw.text((width // 2 - 50, height // 2), f"{symbol} No Data", fill=(255, 255, 255, 255), font=font)
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG")
        return buf.getvalue()

    # Dimensions
    pad_left = 30
    pad_right = 110
    pad_top = 65
    pad_bottom = 45
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    # Extract price bounds
    lows = [c["low"] for c in display_candles]
    highs = [c["high"] for c in display_candles]

    side = str(zone.get("side") or "BUY").upper()
    ob_h_val = zone.get("ob_high")
    ob_l_val = zone.get("ob_low")
    ob_high = float(ob_h_val) if ob_h_val is not None else float(highs[-1])
    ob_low = float(ob_l_val) if ob_l_val is not None else float(lows[-1])

    # 50% Mean Threshold (MT) is the institutional entry
    mt_calc = (ob_high + ob_low) / 2.0
    entry_val = zone.get("mean_threshold") or zone.get("entry_price")
    entry_p = float(entry_val) if entry_val is not None else mt_calc

    # Target TP: +15.0% ROE at 5x = +3.00% price move (Hermes 3.0 Model 2A)
    tp_val = zone.get("tp_price")
    tp_p = float(tp_val) if tp_val is not None else (entry_p * 1.0300 if side in ("BUY", "LONG") else entry_p * 0.9700)

    # Soft SL: -7.5% ROE at 5x = -1.50% price move (Candle Body Close)
    sl_val = zone.get("soft_sl_price") or zone.get("sl_price")
    sl_p = float(sl_val) if sl_val is not None else (entry_p * 0.9850 if side in ("BUY", "LONG") else entry_p * 1.0150)

    # Break-Even Armor: +1.50% price move (+7.5% ROE)
    armor_p = float(zone.get("be_armor_price") or zone.get("armor_stage1_price") or (entry_p * 1.0150 if side in ("BUY", "LONG") else entry_p * 0.9850))

    # Gather all prices for scale (including up to 3 OB zones)
    zones_list = zones[:3] if zones else ([zone] if zone else [])
    all_prices = lows + highs + [entry_p, tp_p, sl_p]
    for z in zones_list:
        if z.get("ob_high") is not None:
            all_prices.append(float(z["ob_high"]))
        if z.get("ob_low") is not None:
            all_prices.append(float(z["ob_low"]))

    min_price = min(all_prices)
    max_price = max(all_prices)
    price_range = max_price - min_price
    if price_range <= 0:
        price_range = max_price * 0.05 or 1.0

    # Add 4% margin top & bottom
    min_price -= price_range * 0.04
    max_price += price_range * 0.04
    total_range = max_price - min_price

    def to_y(p: float) -> int:
        ratio = (p - min_price) / total_range
        return int(pad_top + plot_h - (ratio * plot_h))

    def format_px(p: float) -> str:
        if p >= 100:
            return f"{p:,.2f}"
        elif p >= 1:
            return f"{p:.4f}"
        else:
            return f"{p:.6f}"

    # Draw Background Grid Lines (Horizontal)
    grid_steps = 5
    for i in range(grid_steps + 1):
        gp = min_price + (total_range * (i / grid_steps))
        gy = to_y(gp)
        draw.line([(pad_left, gy), (pad_left + plot_w, gy)], fill=(30, 34, 45, 255), width=1)
        # Price label on right axis
        draw.text((pad_left + plot_w + 8, gy - 6), format_px(gp), fill=(120, 130, 145, 255), font=font)

    # Right Axis separator
    draw.line([(pad_left + plot_w, pad_top), (pad_left + plot_w, pad_top + plot_h)], fill=(42, 46, 57, 255), width=1)

    n_candles = len(display_candles)
    step_x = plot_w / max(1, n_candles)
    candle_w = max(3, int(step_x * 0.65))

    # Pre-calculate x coords
    candle_x_coords = []
    for i in range(n_candles):
        cx = int(pad_left + (i * step_x) + (step_x / 2))
        candle_x_coords.append(cx)

    # Semi-transparent background overlay layer for Order Blocks
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Draw up to 3 Order Blocks as soft, non-intrusive background highlights
    for idx, z in enumerate(zones_list):
        z_side = str(z.get("side") or "BUY").upper()
        z_h = float(z["ob_high"]) if z.get("ob_high") is not None else highs[-1]
        z_l = float(z["ob_low"]) if z.get("ob_low") is not None else lows[-1]
        z_mt = (z_h + z_l) / 2.0

        z_y1 = to_y(z_h)
        z_y2 = to_y(z_l)
        z_ymt = to_y(z_mt)

        if z_y1 > z_y2:
            z_y1, z_y2 = z_y2, z_y1
        if z_y2 - z_y1 < 2:
            z_y2 = z_y1 + 2

        # Start from origin candle position if available in display window, else last 18 candles
        origin_ci = max(0, n_candles - 18)
        z_time = z.get("origin_time")
        if z_time:
            for ci, c in enumerate(display_candles):
                if c.get("time") == z_time:
                    origin_ci = ci
                    break
        
        z_start_x = candle_x_coords[origin_ci]

        # Check if zone is mitigated / tapped at 50% Mean Threshold strictly AFTER origin
        is_mitigated = z.get("status") in ("MITIGATED", "TAPPED", "FILLED")
        mitigation_ci = None
        for ci in range(origin_ci + 1, n_candles):
            c = display_candles[ci]
            if z_side == "BUY" and c["low"] <= z_mt:
                is_mitigated = True
                mitigation_ci = ci
                break
            elif z_side != "BUY" and c["high"] >= z_mt:
                is_mitigated = True
                mitigation_ci = ci
                break

        if is_mitigated and mitigation_ci is not None:
            zone_end_x = candle_x_coords[mitigation_ci]
            status_desc = "🛡️ 50% MT MITIGATED"
            box_border_alpha = 70
        else:
            zone_end_x = pad_left + plot_w
            status_desc = "⚡ LIVE UNMITIGATED (+5 Bars Projection)"
            box_border_alpha = 140

        # GUARANTEE x0 <= x1 and y0 <= y1 to eliminate Pillow "x1 must be >= x0" ValueError
        box_x0 = min(z_start_x, zone_end_x)
        box_x1 = max(z_start_x, zone_end_x)
        if box_x1 - box_x0 < 4:
            box_x1 = box_x0 + 4

        box_y0 = min(z_y1, z_y2)
        box_y1 = max(z_y1, z_y2)
        if box_y1 - box_y0 < 2:
            box_y1 = box_y0 + 2

        # Ultra-light background tint (alpha 24 ~ 9% opacity for crisp visibility)
        if z_side == "BUY":
            box_fill = (0, 230, 118, 22)      # Emerald Green Tint
            box_border = (0, 230, 118, box_border_alpha)
            lbl_color = (0, 230, 118, 220)
            mt_color = (0, 210, 255, 180)     # Cyan MT Line
        else:
            box_fill = (255, 23, 68, 22)      # Crimson Red Tint
            box_border = (255, 23, 68, box_border_alpha)
            lbl_color = (255, 23, 68, 220)
            mt_color = (255, 145, 0, 180)     # Orange MT Line

        overlay_draw.rectangle([box_x0, box_y0, box_x1, box_y1], fill=box_fill, outline=box_border, width=1)
        
        # 50% Mean Threshold (MT) Dashed Line inside OB
        mt_x = box_x0
        while mt_x < box_x1:
            overlay_draw.line([(mt_x, z_ymt), (min(mt_x + 6, box_x1), z_ymt)], fill=mt_color, width=1)
            mt_x += 10

        # Indicator Order Block Badge
        ob_lbl = f"🏛️ HERMES 3.0 {z_side} OB [50% MT: ${format_px(z_mt)}] • {status_desc}"
        overlay_draw.text((box_x0 + 6, box_y0 + 3), ob_lbl, fill=lbl_color, font=font)

    # CRITICAL: Composite OB overlay BEFORE drawing candlesticks
    # This ensures all candle wicks and bodies stay 100% crisp and unobstructed!
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Draw Candlesticks ON TOP of the soft background
    up_color = (8, 153, 129, 255)    # Emerald Green
    down_color = (242, 54, 69, 255)  # Coral Red

    for i, c in enumerate(display_candles):
        cx = candle_x_coords[i]
        c_open = to_y(c["open"])
        c_close = to_y(c["close"])
        c_high = to_y(c["high"])
        c_low = to_y(c["low"])

        is_up = c["close"] >= c["open"]
        color = up_color if is_up else down_color

        # High-Low Wick
        draw.line([(cx, c_high), (cx, c_low)], fill=color, width=1)

        # Body
        top_y = min(c_open, c_close)
        bot_y = max(c_open, c_close)
        if bot_y - top_y < 1:
            bot_y = top_y + 1  # Doji minimum height

        half_w = candle_w // 2
        draw.rectangle([cx - half_w, top_y, cx + half_w, bot_y], fill=color, outline=color)

    # Draw Indicator Trigger Signal Tag on the Tap/Entry Candle
    if candle_x_coords:
        trigger_cx = candle_x_coords[-1]
        action_str = "LONG" if side in ("BUY", "LONG") else "SHORT"
        if action_str == "LONG":
            tag_y = to_y(display_candles[-1]["low"]) + 18
            draw.polygon([(trigger_cx, tag_y - 6), (trigger_cx - 5, tag_y), (trigger_cx + 5, tag_y)], fill=(0, 230, 118, 255))
            draw.text((trigger_cx - 38, tag_y + 2), "⚡ H3.0 BUY", fill=(0, 230, 118, 255), font=font)
        else:
            tag_y = to_y(display_candles[-1]["high"]) - 22
            draw.polygon([(trigger_cx, tag_y + 6), (trigger_cx - 5, tag_y), (trigger_cx + 5, tag_y)], fill=(255, 23, 68, 255))
            draw.text((trigger_cx - 40, tag_y - 12), "⚡ H3.0 SELL", fill=(255, 23, 68, 255), font=font)

    # Draw Target Lines with Badges: Entry, TP, SL
    def draw_level_line(price: float, line_color: tuple, badge_color: tuple, label: str):
        ly = to_y(price)
        # Dashed line across chart
        dash_len = 8
        space_len = 4
        cur_x = pad_left
        while cur_x < pad_left + plot_w:
            draw.line([(cur_x, ly), (min(cur_x + dash_len, pad_left + plot_w), ly)], fill=line_color, width=1)
            cur_x += dash_len + space_len

        # Right Axis Badge
        badge_text = f"{label} {format_px(price)}"
        badge_w = 125
        badge_h = 16
        draw.rectangle(
            [pad_left + plot_w + 2, ly - (badge_h // 2), pad_left + plot_w + 2 + badge_w, ly + (badge_h // 2)],
            fill=badge_color
        )
        draw.text((pad_left + plot_w + 5, ly - 5), badge_text, fill=(255, 255, 255, 255), font=font)

    # Dynamic calculation of TP / SL move percentages
    tp_move_pct = (abs(tp_p - entry_p) / entry_p * 100.0) if entry_p > 0 else 3.0
    sl_move_pct = (abs(sl_p - entry_p) / entry_p * 100.0) if entry_p > 0 else 1.5

    # TP Line (+15.0% ROE / +3.00% price move)
    draw_level_line(tp_p, (0, 230, 118, 220), (0, 180, 80, 255), f"TP (+15% ROE):")
    # Break-Even Armor Trigger Line (+7.5% ROE -> BE Lock at Entry)
    draw_level_line(armor_p, (0, 229, 255, 220), (0, 140, 200, 255), f"BE ARMOR (+7.5%):")
    # 50% Mean Threshold Entry Line
    draw_level_line(entry_p, (245, 158, 11, 240), (200, 130, 10, 255), "50% MT ENTRY:")
    # Soft SL Line (-7.5% ROE / -1.50% Candle Body Close)
    draw_level_line(sl_p, (255, 82, 82, 220), (220, 40, 40, 255), f"SOFT SL (-7.5%):")

    # Header Banner (Top bar)
    draw.rectangle([0, 0, width, 52], fill=(18, 22, 32, 255))
    draw.line([(0, 52), (width, 52)], fill=(42, 46, 57, 255), width=1)

    # Symbol & Timeframe
    draw.text((24, 18), f"{symbol}  {timeframe.upper()}", fill=(255, 255, 255, 255), font=font)

    # Signal Direction Badge: HERMES 3.0 MODEL 2A
    action_str = "LONG" if side in ("BUY", "LONG") else "SHORT"
    side_badge_text = f"HERMES 3.0 MODEL 2A {action_str}"
    badge_x = 160
    badge_w = 230
    badge_bg = (8, 153, 129, 255) if action_str == "LONG" else (242, 54, 69, 255)
    draw.rectangle([badge_x, 14, badge_x + badge_w, 38], fill=badge_bg)
    draw.text((badge_x + 8, 21), side_badge_text, fill=(255, 255, 255, 255), font=font)

    # Current / Trigger Price
    cur_px_text = f"50% MT: ${format_px(entry_p)} | TP: ${format_px(tp_p)} (+15%) | Soft SL: ${format_px(sl_p)} (-7.5%)"
    draw.text((badge_x + badge_w + 15, 21), cur_px_text, fill=(200, 210, 225, 255), font=font)

    # Sentries HUD Overlay Box in upper right corner of plot
    hud_x = pad_left + plot_w - 290
    hud_y = pad_top + 10
    draw.rectangle([hud_x, hud_y, hud_x + 280, hud_y + 36], fill=(15, 20, 30, 220), outline=(55, 65, 81, 255))
    draw.text((hud_x + 8, hud_y + 4), "🛡️ HERMES 3.0 MODEL 2A ARMED", fill=(56, 189, 248, 255), font=font)
    draw.text((hud_x + 8, hud_y + 19), "S1: BTC OK | S2: Disp>=5% | S3: 50% MT | S4: Fresh<=28b", fill=(148, 163, 184, 255), font=font)

    # Watermark Footer
    now_str = get_ist_now().strftime("%d %b %Y %I:%M %p IST")
    watermark = f"HERMES 3.0 MODEL 2A QUANT ENGINE | DUAL-THRESHOLD INSTITUTIONAL | {timeframe.upper()} BINANCE FUTURES | {now_str}"
    draw.text((pad_left, height - 25), watermark, fill=(100, 115, 135, 255), font=font)


    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", quality=95)
    return buf.getvalue()
