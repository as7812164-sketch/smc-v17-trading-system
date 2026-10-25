import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

def generate_hermes_icon(size: int) -> Image.Image:
    # High-resolution rendering canvas (2x super-sampling for crisp edges)
    s = size * 2
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Dark Futuristic Rounded Background
    radius = int(s * 0.22)
    # Background gradient approximation using nested rectangles
    bg_color = (11, 14, 20, 255) # Deep obsidian dark
    draw.rounded_rectangle([0, 0, s, s], radius=radius, fill=bg_color)

    # Subtle glowing outer border
    border_color = (0, 240, 255, 180) # Cyber Cyan
    draw.rounded_rectangle([int(s*0.02), int(s*0.02), int(s*0.98), int(s*0.98)], radius=radius, outline=border_color, width=max(2, int(s*0.02)))

    # 2. Glowing Golden Candlesticks & Apex Wing Motif
    cx = s // 2
    cy = s // 2

    # Draw Bullish Candlestick (Gold)
    gold = (245, 184, 0, 255)
    c1_w = int(s * 0.08)
    c1_h = int(s * 0.32)
    c1_x = cx - int(s * 0.14)
    c1_y = cy - int(s * 0.12)
    # Wick
    draw.line([(c1_x + c1_w // 2, c1_y - int(s * 0.10)), (c1_x + c1_w // 2, c1_y + c1_h + int(s * 0.10))], fill=gold, width=max(2, int(s*0.015)))
    # Body
    draw.rectangle([c1_x, c1_y, c1_x + c1_w, c1_y + c1_h], fill=gold)

    # Draw Bearish Candlestick (Cyan/Purple Apex)
    cyan = (0, 229, 255, 255)
    c2_w = int(s * 0.08)
    c2_h = int(s * 0.44)
    c2_x = cx + int(s * 0.06)
    c2_y = cy - int(s * 0.24)
    # Wick
    draw.line([(c2_x + c2_w // 2, c2_y - int(s * 0.08)), (c2_x + c2_w // 2, c2_y + c2_h + int(s * 0.08))], fill=cyan, width=max(2, int(s*0.015)))
    # Body
    draw.rectangle([c2_x, c2_y, c2_x + c2_w, c2_y + c2_h], fill=cyan)

    # Apex Triangular Chevron over candlesticks
    accent = (255, 255, 255, 240)
    pt1 = (cx, int(s * 0.14))
    pt2 = (int(s * 0.22), int(s * 0.36))
    pt3 = (int(s * 0.78), int(s * 0.36))
    draw.line([pt2, pt1, pt3], fill=(0, 240, 255, 220), width=max(3, int(s * 0.025)))

    # Hermes Wing / Feather Accents
    draw.arc([int(s * 0.15), int(s * 0.45), int(s * 0.85), int(s * 0.85)], start=30, end=150, fill=gold, width=max(3, int(s * 0.025)))

    # Downsample cleanly to target size (Lanczos filtering)
    final_img = img.resize((size, size), Image.Resampling.LANCZOS)
    return final_img

# Generate 192x192, 512x512, and 180x180
icon192 = generate_hermes_icon(192)
icon192.save(STATIC_DIR / "icon-192.png", "PNG")

icon512 = generate_hermes_icon(512)
icon512.save(STATIC_DIR / "icon-512.png", "PNG")

icon180 = generate_hermes_icon(180)
icon180.save(STATIC_DIR / "apple-touch-icon.png", "PNG")

# Favicon
icon192.save(STATIC_DIR / "favicon.ico", format="ICO", sizes=[(32, 32), (48, 48), (64, 64)])

print("Successfully generated all PWA icons in static/")
