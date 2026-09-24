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

    entry_val = zone.get("entry_price")
    if entry_val is not None:
        entry_p = float(entry_val)
    else:
        entry_p = ob_high if side == "BUY" else ob_low

    tp_val = zone.get("tp_price")
    if tp_val is not None:
        tp_p = float(tp_val)
    else:
        tp_p = entry_p * 1.04 if side == "BUY" else entry_p * 0.96

    sl_val = zone.get("sl_price")
    if sl_val is not None:
        sl_p = float(sl_val)
    else:
        sl_p = entry_p * 0.97 if side == "BUY" else entry_p * 1.03

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

        z_y1 = to_y(z_h)
        z_y2 = to_y(z_l)
        if z_y1 > z_y2:
            z_y1, z_y2 = z_y2, z_y1
        if z_y2 - z_y1 < 2:
            z_y2 = z_y1 + 2

        # Start from origin candle position if available in display window, else last 16 candles
        z_start_x = candle_x_coords[max(0, n_candles - 18)]
        z_time = z.get("origin_time")
        if z_time:
            for ci, c in enumerate(display_candles):
                if c.get("time") == z_time:
                    z_start_x = candle_x_coords[ci]
                    break
        zone_end_x = pad_left + plot_w

        # Ultra-light background tint (alpha 18 ~ 7% opacity for zero noise)
        if z_side == "BUY":
            box_fill = (8, 153, 129, 18)     # Soft Light Green
            box_border = (8, 153, 129, 75)    # Subtle 1px border
            lbl_color = (8, 153, 129, 170)
        else:
            box_fill = (242, 54, 69, 18)     # Soft Light Red
            box_border = (242, 54, 69, 75)    # Subtle 1px border
            lbl_color = (242, 54, 69, 170)

        overlay_draw.rectangle([z_start_x, z_y1, zone_end_x, z_y2], fill=box_fill, outline=box_border, width=1)
        # Clean muted label
        ob_lbl = f"4H {z_side} OB #{idx+1} [${format_px(z_l)} - ${format_px(z_h)}]"
        overlay_draw.text((z_start_x + 6, z_y1 + 3), ob_lbl, fill=lbl_color, font=font)

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
        badge_text = f"{label}: {format_px(price)}"
        badge_w = 104
        badge_h = 16
        draw.rectangle(
            [pad_left + plot_w + 2, ly - (badge_h // 2), pad_left + plot_w + 2 + badge_w, ly + (badge_h // 2)],
            fill=badge_color
        )
        draw.text((pad_left + plot_w + 6, ly - 5), badge_text, fill=(255, 255, 255, 255), font=font)

    # TP Line (+4%)
    draw_level_line(tp_p, (0, 230, 118, 220), (0, 180, 80, 255), "TP (+4%)")
    # Entry Line
    draw_level_line(entry_p, (0, 210, 255, 240), (0, 140, 200, 255), "ENTRY")
    # SL Line (-3%)
    draw_level_line(sl_p, (255, 82, 82, 220), (220, 40, 40, 255), "SL (-3%)")

    # Header Banner (Top bar)
    draw.rectangle([0, 0, width, 52], fill=(18, 22, 32, 255))
    draw.line([(0, 52), (width, 52)], fill=(42, 46, 57, 255), width=1)

    # Symbol & Timeframe
    draw.text((24, 18), f"{symbol}  {timeframe}", fill=(255, 255, 255, 255), font=font)

    # Signal Direction Badge
    side_badge_text = f"SMC V17 FIRST TAP {side}"
    badge_x = 180
    badge_w = 180
    badge_bg = (8, 153, 129, 255) if side == "BUY" else (242, 54, 69, 255)
    draw.rectangle([badge_x, 14, badge_x + badge_w, 38], fill=badge_bg)
    draw.text((badge_x + 12, 21), side_badge_text, fill=(255, 255, 255, 255), font=font)

    # Current / Trigger Price
    cur_px_text = f"Trigger: ${format_px(entry_p)}  |  TP: ${format_px(tp_p)}  |  SL: ${format_px(sl_p)}"
    draw.text((badge_x + badge_w + 20, 21), cur_px_text, fill=(200, 210, 225, 255), font=font)

    # Watermark Footer
    now_str = get_ist_now().strftime("%d %b %Y %I:%M %p IST")
    watermark = f"SMC V17 AI AGENT | BINANCE FUTURES 4H | {now_str}"
    draw.text((pad_left, height - 25), watermark, fill=(80, 90, 105, 255), font=font)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", quality=95)
    return buf.getvalue()
