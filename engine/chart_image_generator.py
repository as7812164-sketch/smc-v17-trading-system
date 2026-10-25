import io
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
from config import get_ist_now


def get_font(size: int = 12, bold: bool = False) -> ImageFont.ImageFont:
    """Helper to load standard fonts across Windows and Linux, fallback to default."""
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "arial.ttf"
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            pass
    return ImageFont.load_default()


def render_smc_chart_image(
    symbol: str,
    candles: List[Dict[str, Any]],
    zone: Dict[str, Any],
    zones: Optional[List[Dict[str, Any]]] = None,
    timeframe: str = "1H"
) -> bytes:
    """
    Renders a high-resolution, professional LIGHT-THEMED TradingView candlestick chart
    specifically for Hermes 3.5 Radar Harvest with Order Block 5% boundary penetration,
    0.20% proximity radar, Take Profit (+29% Target), 6-Tier Trailing SL, and Entry badge.
    Returns in-memory PNG bytes.
    """
    width = 1000
    height = 580

    # 1. Canvas Background: Pure Clean White (Light Mode)
    bg_color = (255, 255, 255, 255)
    img = Image.new("RGBA", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Fonts
    font_title = get_font(15, bold=True)
    font_bold = get_font(12, bold=True)
    font_regular = get_font(11, bold=False)
    font_small = get_font(10, bold=False)

    # Display last 48 candles for clean candlestick spacing
    display_candles = candles[-48:] if len(candles) > 48 else candles
    if not display_candles:
        draw.text((width // 2 - 60, height // 2), f"{symbol} No Market Data", fill=(100, 116, 139, 255), font=font_bold)
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG")
        return buf.getvalue()

    # Layout Paddings
    pad_left = 35
    pad_right = 140
    pad_top = 70
    pad_bottom = 40
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    # Bounds
    lows = [float(c["low"]) for c in display_candles]
    highs = [float(c["high"]) for c in display_candles]

    side = str(zone.get("side") or "BUY").upper()
    is_long = side in ("BUY", "LONG")

    ob_h_val = zone.get("ob_high")
    ob_l_val = zone.get("ob_low")
    ob_high = float(ob_h_val) if ob_h_val is not None else float(highs[-1])
    ob_low = float(ob_l_val) if ob_l_val is not None else float(lows[-1])
    ob_rng = abs(ob_high - ob_low)

    # Hermes 3.5: 5% Boundary Penetration Entry
    if is_long:
        calc_entry = ob_high - (ob_rng * 0.05)
        calc_radar = calc_entry * 1.0020
    else:
        calc_entry = ob_low + (ob_rng * 0.05)
        calc_radar = calc_entry * 0.9980

    entry_p = float(zone.get("entry_price") or calc_entry)
    radar_p = float(zone.get("radar_price") or calc_radar)

    # TP: +29.0% Harvest Target (5.80% move at 5x)
    tp_val = zone.get("tp_price")
    tp_p = float(tp_val) if tp_val is not None else (entry_p * 1.0580 if is_long else entry_p * 0.9420)

    # Step 1 Trailing SL: +4.90% trigger -> +0.50% lock
    step1_lock_p = round(entry_p * (1.0 + 0.0010), 8) if is_long else round(entry_p * (1.0 - 0.0010), 8)

    # Initial SL (-7.5% ROI at 5x / -1.50% move)
    sl_val = zone.get("hard_sl_price") or zone.get("sl_price")
    sl_p = float(sl_val) if sl_val is not None else (entry_p * 0.9850 if is_long else entry_p * 1.0150)

    # Price scaling
    zones_list = zones[:3] if zones else ([zone] if zone else [])
    all_prices = lows + highs + [entry_p, tp_p, sl_p, radar_p]
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

    min_price -= price_range * 0.05
    max_price += price_range * 0.05
    total_range = max_price - min_price

    def to_y(p: float) -> int:
        ratio = (p - min_price) / total_range
        return int(pad_top + plot_h - (ratio * plot_h))

    def format_px(p: float) -> str:
        if p >= 1000:
            return f"{p:,.2f}"
        elif p >= 10:
            return f"{p:.3f}"
        elif p >= 1:
            return f"{p:.4f}"
        else:
            return f"{p:.6f}"

    # 2. Draw Subtle Horizontal Grid Lines
    grid_steps = 6
    for i in range(grid_steps + 1):
        gp = min_price + (total_range * (i / grid_steps))
        gy = to_y(gp)
        # Very light dashed gray grid
        draw.line([(pad_left, gy), (pad_left + plot_w, gy)], fill=(241, 245, 249, 255), width=1)
        # Price on right axis
        draw.text((pad_left + plot_w + 10, gy - 7), format_px(gp), fill=(148, 163, 184, 255), font=font_small)

    # Right Axis separator line
    draw.line([(pad_left + plot_w, pad_top), (pad_left + plot_w, pad_top + plot_h)], fill=(226, 232, 240, 255), width=1)

    n_candles = len(display_candles)
    step_x = plot_w / max(1, n_candles)
    candle_w = max(4, int(step_x * 0.68))

    candle_x_coords = []
    for i in range(n_candles):
        cx = int(pad_left + (i * step_x) + (step_x / 2))
        candle_x_coords.append(cx)

    # 3. Translucent Overlay for Order Block Shading
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    for idx, z in enumerate(zones_list):
        z_side = str(z.get("side") or "BUY").upper()
        z_is_buy = z_side in ("BUY", "LONG")
        z_h = float(z["ob_high"]) if z.get("ob_high") is not None else highs[-1]
        z_l = float(z["ob_low"]) if z.get("ob_low") is not None else lows[-1]
        z_rng = abs(z_h - z_l)

        z_ent = float(z.get("entry_price") or (z_h - z_rng * 0.05 if z_is_buy else z_l + z_rng * 0.05))
        z_rad = float(z.get("radar_price") or (z_ent * 1.0020 if z_is_buy else z_ent * 0.9980))

        z_y1 = to_y(max(z_h, z_l))
        z_y2 = to_y(min(z_h, z_l))

        origin_ci = max(0, n_candles - 16)
        z_time = z.get("origin_time")
        if z_time:
            for ci, c in enumerate(display_candles):
                if c.get("time") == z_time:
                    origin_ci = ci
                    break

        z_start_x = candle_x_coords[origin_ci]
        zone_end_x = pad_left + plot_w

        box_x0 = min(z_start_x, zone_end_x)
        box_x1 = max(z_start_x, zone_end_x)
        box_y0 = min(z_y1, z_y2)
        box_y1 = max(z_y1, z_y2)
        if box_y1 - box_y0 < 3:
            box_y1 = box_y0 + 3

        # Light Theme Translucent Fills (Crisp Emerald Green for Demand, Soft Rose Red for Supply)
        if z_is_buy:
            ob_fill = (16, 185, 129, 32)      # Soft Emerald
            ob_border = (16, 185, 129, 150)
            tag_color = (5, 150, 105, 255)
        else:
            ob_fill = (239, 68, 68, 32)       # Soft Crimson
            ob_border = (239, 68, 68, 150)
            tag_color = (220, 38, 38, 255)

        overlay_draw.rectangle([box_x0, box_y0, box_x1, box_y1], fill=ob_fill, outline=ob_border, width=1)

        # 5% Boundary Penetration Line (Dashed Amber Gold #F59E0B)
        y_ent = to_y(z_ent)
        cur_x = box_x0
        while cur_x < box_x1:
            overlay_draw.line([(cur_x, y_ent), (min(cur_x + 6, box_x1), y_ent)], fill=(245, 158, 11, 240), width=2)
            cur_x += 10

        # 0.20% Proximity Radar Line (Dotted Cyan #0284C7)
        y_rad = to_y(z_rad)
        cur_x = box_x0
        while cur_x < box_x1:
            overlay_draw.line([(cur_x, y_rad), (min(cur_x + 3, box_x1), y_rad)], fill=(2, 132, 199, 200), width=1)
            cur_x += 6

    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # 4. Draw Candlesticks ON TOP (High contrast for Light Mode)
    up_candle_color = (16, 185, 129, 255)    # TradingView Green #10B981
    down_candle_color = (239, 68, 68, 255)   # TradingView Red #EF4444

    for i, c in enumerate(display_candles):
        cx = candle_x_coords[i]
        c_open = to_y(float(c["open"]))
        c_close = to_y(float(c["close"]))
        c_high = to_y(float(c["high"]))
        c_low = to_y(float(c["low"]))

        is_up = float(c["close"]) >= float(c["open"])
        c_color = up_candle_color if is_up else down_candle_color

        # Candle Wick
        draw.line([(cx, c_high), (cx, c_low)], fill=c_color, width=1)

        # Candle Body
        top_y = min(c_open, c_close)
        bot_y = max(c_open, c_close)
        if bot_y - top_y < 1:
            bot_y = top_y + 1

        half_w = candle_w // 2
        draw.rectangle([cx - half_w, top_y, cx + half_w, bot_y], fill=c_color, outline=c_color)

    # 5. Draw Helper Level Lines Across Chart
    def draw_light_level(price: float, line_color: tuple, badge_bg: tuple, badge_text: str):
        ly = to_y(price)
        cur_x = pad_left
        while cur_x < pad_left + plot_w:
            draw.line([(cur_x, ly), (min(cur_x + 6, pad_left + plot_w), ly)], fill=line_color, width=1)
            cur_x += 10

        # Right Axis Badge (Light theme with solid pill)
        badge_w = 135
        badge_h = 18
        bx0 = pad_left + plot_w + 3
        by0 = ly - (badge_h // 2)
        bx1 = bx0 + badge_w
        by1 = by0 + badge_h

        draw.rectangle([bx0, by0, bx1, by1], fill=badge_bg)
        draw.text((bx0 + 6, by0 + 3), badge_text, fill=(255, 255, 255, 255), font=font_small)

    # Draw Levels:
    # TP Target (+29.0% Harvest Target)
    draw_light_level(tp_p, (16, 185, 129, 220), (16, 185, 129, 255), f"🎯 TP (+29%): {format_px(tp_p)}")
    # 5% Boundary Entry Line
    draw_light_level(entry_p, (245, 158, 11, 240), (217, 119, 6, 255), f"⚡ ENTRY (5%): {format_px(entry_p)}")
    # Initial SL
    draw_light_level(sl_p, (239, 68, 68, 220), (220, 38, 38, 255), f"🛑 INITIAL SL: {format_px(sl_p)}")

    # 6. Entry Execution Tag on Trigger Candle
    if candle_x_coords:
        trigger_cx = candle_x_coords[-1]
        action_text = "🟢 BUY ENTRY" if is_long else "🔴 SELL ENTRY"
        if is_long:
            tag_y = to_y(float(display_candles[-1]["low"])) + 22
            draw.polygon([(trigger_cx, tag_y - 6), (trigger_cx - 5, tag_y), (trigger_cx + 5, tag_y)], fill=(16, 185, 129, 255))
            draw.rectangle([trigger_cx - 48, tag_y, trigger_cx + 48, tag_y + 16], fill=(16, 185, 129, 255))
            draw.text((trigger_cx - 44, tag_y + 2), action_text, fill=(255, 255, 255, 255), font=font_small)
        else:
            tag_y = to_y(float(display_candles[-1]["high"])) - 24
            draw.polygon([(trigger_cx, tag_y + 6), (trigger_cx - 5, tag_y), (trigger_cx + 5, tag_y)], fill=(239, 68, 68, 255))
            draw.rectangle([trigger_cx - 48, tag_y - 16, trigger_cx + 48, tag_y], fill=(239, 68, 68, 255))
            draw.text((trigger_cx - 44, tag_y - 14), action_text, fill=(255, 255, 255, 255), font=font_small)

    # 7. Header Top Banner (Clean Crisp Light Slate)
    draw.rectangle([0, 0, width, 56], fill=(248, 250, 252, 255))
    draw.line([(0, 56), (width, 56)], fill=(226, 232, 240, 255), width=1)

    # Symbol & Timeframe
    draw.text((25, 16), f"#{symbol.upper()} • {timeframe.upper()}", fill=(15, 23, 42, 255), font=font_title)

    # Action Badge
    action_str = "LONG BUY" if is_long else "SHORT SELL"
    badge_bg = (16, 185, 129, 255) if is_long else (239, 68, 68, 255)
    badge_x = 210
    badge_w = 120
    draw.rectangle([badge_x, 14, badge_x + badge_w, 40], fill=badge_bg)
    draw.text((badge_x + 12, 19), f"⚡ {action_str}", fill=(255, 255, 255, 255), font=font_bold)

    # Strategy Title
    draw.text((badge_x + badge_w + 16, 14), "HERMES 3.5 RADAR HARVEST • 5% BOUNDARY", fill=(15, 23, 42, 255), font=font_bold)
    draw.text((badge_x + badge_w + 16, 32), f"Fill: ${format_px(entry_p)} | 6-Tier Trailing SL Active | TP: +29% ROE Target", fill=(71, 85, 105, 255), font=font_small)

    # 8. Strategy HUD Card (Light Theme Box in upper right of chart)
    hud_x = pad_left + plot_w - 360
    hud_y = pad_top + 10
    draw.rectangle([hud_x, hud_y, hud_x + 350, hud_y + 38], fill=(255, 255, 255, 240), outline=(203, 213, 225, 255))
    draw.text((hud_x + 10, hud_y + 4), "🛡️ 6-TIER STEPPED TRAILING SL LADDER ACTIVE", fill=(2, 132, 199, 255), font=font_bold)
    draw.text((hud_x + 10, hud_y + 20), "+4.9%➔+0.5% | +9.8%➔+5.1% | +14.8%➔+10.1% | +19.8%➔+15.1% | +24%➔+20.1% | +29%➔+25%", fill=(100, 116, 139, 255), font=font_small)

    # 9. Watermark Footer (Light Theme)
    now_str = get_ist_now().strftime("%d %b %Y • %I:%M %p IST")
    footer_text = f"HERMES 3.5 RADAR HARVEST QUANT TERMINAL | LIGHT THEME OFFICIAL ALERT | {timeframe.upper()} BINANCE FEED | {now_str}"
    draw.text((pad_left, height - 25), footer_text, fill=(148, 163, 184, 255), font=font_small)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", quality=95)
    return buf.getvalue()
