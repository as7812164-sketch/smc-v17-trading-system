with open("static/mobile.html", "r", encoding="utf-8") as f:
    html = f.read()

bottom_nav_css = """        /* =========================================================
           NATIVE BOTTOM NAVIGATION BAR (FIXED DOCK)
           ========================================================= */
        .bottom-nav {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            width: 100% !important;
            max-width: 100vw !important;
            height: 76px !important;
            background: #0B0F17 !important;
            backdrop-filter: blur(24px) !important;
            -webkit-backdrop-filter: blur(24px) !important;
            border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
            display: flex !important;
            justify-content: space-around !important;
            align-items: center !important;
            z-index: 999999 !important;
            box-shadow: 0 -8px 30px rgba(0, 0, 0, 0.85) !important;
            transform: translateZ(0) !important;
            -webkit-transform: translateZ(0) !important;
            box-sizing: border-box !important;
            padding-bottom: env(safe-area-inset-bottom, 6px) !important;
            padding-top: 4px !important;
        }

        .nav-item {
            flex: 1 !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 4px !important;
            background: none !important;
            border: none !important;
            color: #94A3B8 !important;
            font-size: 13.5px !important;
            font-weight: 700 !important;
            letter-spacing: 0.2px !important;
            cursor: pointer !important;
            padding: 6px 0 !important;
            position: relative !important;
            user-select: none !important;
            -webkit-user-select: none !important;
            transition: all 0.2s ease !important;
        }

        .nav-item i {
            font-size: 26px !important;
            transition: all 0.2s ease !important;
        }

        .nav-item span {
            font-size: 13px !important;
            font-weight: 700 !important;
        }

        .nav-item:active {
            transform: scale(0.92) !important;
        }

        .nav-item.active {
            color: #00F59B !important;
        }

        .nav-item.active i {
            color: #00F59B !important;
            transform: scale(1.12) !important;
            filter: drop-shadow(0 0 10px rgba(0, 245, 155, 0.6)) !important;
        }

        .nav-item.active span {
            color: #00F59B !important;
            font-weight: 900 !important;
        }
"""

# Replace existing .nav-item CSS with full bottom-nav CSS
idx_nav_item = html.find(".nav-item {")
idx_nav_item_end = html.find(".nav-item.active i {")
if idx_nav_item_end != -1:
    idx_close = html.find("}", idx_nav_item_end)
    if idx_close != -1:
        html = html[:idx_nav_item] + bottom_nav_css + "\n\n        " + html[idx_close + 1:]
        print("Replaced and restored bottom-nav CSS!")

# Ensure body padding-bottom is 96px so content is never hidden behind the nav bar
if "padding-bottom: 96px !important;" not in html:
    html = html.replace("padding-bottom: 80px", "padding-bottom: 96px !important")

with open("static/mobile.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Saved updated static/mobile.html with restored bottom-nav!")
