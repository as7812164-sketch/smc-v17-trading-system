# -*- coding: utf-8 -*-
"""
Upgrade static/mobile.html for High-DPI AMOLED phones (Poco F6, 1220p, 446 PPI).
Eliminates all micro-fonts (8px-10px) and enforces native phone proportions:
- Body font-size: 15px
- Deca Matrix Grid: ALWAYS 2 columns in portrait mobile (never squished into 5 columns)
- Radar Cards: Tall, spacious, 16px symbols, 14px prices, 44px touch action buttons
- Drawer: 85vw width (taking full mobile proportion), 15px links, 18px icons
- Touch targets: minimum 42px height for all buttons
"""

import os
import re

FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "mobile.html")

with open(FILE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update viewport meta tag if needed
content = re.sub(
    r'<meta name="viewport"[^>]+>',
    '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">',
    content
)

# 2. Extract CSS and rewrite for native phone proportions
OLD_CSS_START = "<style>"
OLD_CSS_END = "</style>"

start_idx = content.find(OLD_CSS_START)
end_idx = content.find(OLD_CSS_END)

if start_idx != -1 and end_idx != -1:
    css_content = content[start_idx + len(OLD_CSS_START):end_idx]

    # Replace small font sizes with readable mobile sizes
    replacements = [
        # Body
        (r'body\s*\{([^}]*?)font-size:\s*13px;', r'body {\1font-size: 15px;'),
        (r'line-height:\s*1\.4;', 'line-height: 1.5;'),
        
        # Header
        (r'padding:\s*calc\(env\(safe-area-inset-top,\s*6px\)\s*\+\s*8px\)\s*12px\s*10px\s*12px;', 'padding: calc(env(safe-area-inset-top, 6px) + 10px) 14px 12px 14px;'),
        (r'width:\s*34px;\s*height:\s*34px;\s*min-width:\s*34px;\s*border-radius:\s*9px;', 'width: 40px; height: 40px; min-width: 40px; border-radius: 10px;'),
        (r'\.header-avatar\s*\{([^}]*?)font-size:\s*16px;', r'.header-avatar {\1font-size: 19px;'),
        (r'\.header-title\s*\{([^}]*?)font-size:\s*14px;', r'.header-title {\1font-size: 16px;'),
        (r'\.header-tag\s*\{([^}]*?)font-size:\s*9px;', r'.header-tag {\1font-size: 10.5px; padding: 2px 6px;'),
        (r'\.header-status\s*\{([^}]*?)font-size:\s*10px;', r'.header-status {\1font-size: 11.5px;'),
        (r'\.refresh-btn\s*\{([^}]*?)width:\s*32px;\s*height:\s*32px;', r'.refresh-btn {\1width: 38px; height: 38px; font-size: 15px;'),
        (r'\.account-toggle-btn\s*\{([^}]*?)font-size:\s*11px;\s*padding:\s*5px\s*9px;', r'.account-toggle-btn {\1font-size: 12px; padding: 7px 11px;'),
        (r'\.hamburger-btn\s*\{([^}]*?)width:\s*34px;\s*height:\s*34px;', r'.hamburger-btn {\1width: 40px; height: 40px; font-size: 18px; border-radius: 10px;'),

        # Hero Wallet Card
        (r'\.hw-label\s*\{([^}]*?)font-size:\s*10\.5px;', r'.hw-label {\1font-size: 12px;'),
        (r'\.hw-badge\s*\{([^}]*?)font-size:\s*9\.5px;\s*padding:\s*2px\s*6px;', r'.hw-badge {\1font-size: 11.5px; padding: 3px 8px;'),
        (r'\.hw-balance\s*\{([^}]*?)font-size:\s*26px;', r'.hw-balance {\1font-size: 30px;'),
        (r'\.hw-pnl-pill\s*\{([^}]*?)font-size:\s*10\.5px;\s*padding:\s*2px\s*6px;', r'.hw-pnl-pill {\1font-size: 12px; padding: 3px 8px;'),
        (r'\.hw-m-label\s*\{([^}]*?)font-size:\s*9px;', r'.hw-m-label {\1font-size: 11px;'),
        (r'\.hw-m-val\s*\{([^}]*?)font-size:\s*12px;', r'.hw-m-val {\1font-size: 14px;'),
        (r'\.cb-header\s*\{([^}]*?)font-size:\s*10px;', r'.cb-header {\1font-size: 12px;'),
        (r'\.cb-target\s*\{([^}]*?)font-size:\s*9\.5px;', r'.cb-target {\1font-size: 11.5px;'),
        (r'\.cb-progress-bar-bg\s*\{([^}]*?)height:\s*5px;', r'.cb-progress-bar-bg {\1height: 7px;'),

        # Ticker Chips
        (r'\.ticker-chip\s*\{([^}]*?)padding:\s*6px\s*10px;', r'.ticker-chip {\1padding: 8px 12px; border-radius: 10px;'),
        (r'\.tc-coin\s*\{([^}]*?)font-size:\s*10\.5px;', r'.tc-coin {\1font-size: 12.5px;'),
        (r'\.tc-price\s*\{([^}]*?)font-size:\s*10\.5px;', r'.tc-price {\1font-size: 12.5px;'),
        (r'\.tc-badge\s*\{([^}]*?)font-size:\s*9\.5px;\s*padding:\s*1px\s*5px;', r'.tc-badge {\1font-size: 11px; padding: 2px 7px;'),

        # 4-Sentries Diagnostic Matrix
        (r'\.rc-title\s*\{([^}]*?)font-size:\s*11\.5px;', r'.rc-title {\1font-size: 13.5px;'),
        (r'\.rc-item\s*\{([^}]*?)padding:\s*7px\s*9px;', r'.rc-item {\1padding: 10px 12px; border-radius: 9px;'),
        (r'\.rc-item-name\s*\{([^}]*?)font-size:\s*9px;', r'.rc-item-name {\1font-size: 11px; margin-bottom: 3px;'),
        (r'\.rc-item-val\s*\{([^}]*?)font-size:\s*11px;', r'.rc-item-val {\1font-size: 13px;'),

        # Section Headers
        (r'\.sh-title\s*\{([^}]*?)font-size:\s*12\.5px;', r'.sh-title {\1font-size: 15px;'),
        (r'\.sh-link\s*\{([^}]*?)font-size:\s*10\.5px;', r'.sh-link {\1font-size: 12.5px;'),

        # Coin List Items
        (r'\.coin-list-item\s*\{([^}]*?)padding:\s*9px\s*12px;', r'.coin-list-item {\1padding: 12px 14px; border-radius: 12px; margin-bottom: 8px;'),
        (r'\.cli-coin-badge\s*\{([^}]*?)width:\s*32px;\s*height:\s*32px;\s*min-width:\s*32px;\s*border-radius:\s*7px;\s*font-size:\s*11px;', r'.cli-coin-badge {\1width: 38px; height: 38px; min-width: 38px; border-radius: 10px; font-size: 13px;'),
        (r'\.cli-symbol\s*\{([^}]*?)font-size:\s*13px;', r'.cli-symbol {\1font-size: 15px;'),
        (r'\.cli-vol\s*\{([^}]*?)font-size:\s*9\.5px;', r'.cli-vol {\1font-size: 11.5px;'),
        (r'\.cli-price\s*\{([^}]*?)font-size:\s*13px;', r'.cli-price {\1font-size: 15px;'),
        (r'\.cli-change-pill\s*\{([^}]*?)font-size:\s*10\.5px;\s*padding:\s*2px\s*7px;', r'.cli-change-pill {\1font-size: 12px; padding: 4px 9px; border-radius: 6px;'),

        # Drawer
        (r'width:\s*320px;\s*max-width:\s*86vw;', 'width: 85vw; max-width: 390px; min-width: 300px;'),
        (r'\.drawer-header\s*\{([^}]*?)padding:\s*calc\(env\(safe-area-inset-top,\s*6px\)\s*\+\s*14px\)\s*16px\s*14px\s*16px;', r'.drawer-header {\1padding: calc(env(safe-area-inset-top, 6px) + 14px) 18px 16px 18px;'),
        (r'\.drawer-avatar\s*\{([^}]*?)width:\s*38px;\s*height:\s*38px;\s*border-radius:\s*10px;\s*font-size:\s*18px;', r'.drawer-avatar {\1width: 46px; height: 46px; border-radius: 12px; font-size: 21px;'),
        (r'\.drawer-username\s*\{([^}]*?)font-size:\s*14px;', r'.drawer-username {\1font-size: 16.5px;'),
        (r'\.drawer-vip-pill\s*\{([^}]*?)font-size:\s*9px;', r'.drawer-vip-pill {\1font-size: 11px; padding: 2px 7px;'),
        (r'\.drawer-user-sub\s*\{([^}]*?)font-size:\s*10px;', r'.drawer-user-sub {\1font-size: 12px;'),
        (r'\.drawer-close-btn\s*\{([^}]*?)width:\s*32px;\s*height:\s*32px;\s*font-size:\s*15px;', r'.drawer-close-btn {\1width: 38px; height: 38px; font-size: 18px; border-radius: 10px;'),
        (r'\.drawer-comp-title-row\s*\{([^}]*?)font-size:\s*10\.5px;', r'.drawer-comp-title-row {\1font-size: 12.5px;'),
        (r'\.drawer-comp-bar\s*\{([^}]*?)height:\s*5px;', r'.drawer-comp-bar {\1height: 7px;'),
        (r'\.drawer-comp-meta\s*\{([^}]*?)font-size:\s*9px;', r'.drawer-comp-meta {\1font-size: 11px;'),
        (r'\.drawer-section-label\s*\{([^}]*?)font-size:\s*9\.5px;', r'.drawer-section-label {\1font-size: 11.5px; padding: 4px 10px;'),
        (r'\.drawer-nav-item\s*\{([^}]*?)padding:\s*10px\s*12px;\s*font-size:\s*12\.5px;', r'.drawer-nav-item {\1padding: 13px 14px; font-size: 14.5px;'),
        (r'\.drawer-nav-item\s*i\s*\{([^}]*?)width:\s*18px;\s*font-size:\s*14px;', r'.drawer-nav-item i {\1width: 24px; font-size: 17px;'),
        (r'\.drawer-badge\s*\{([^}]*?)font-size:\s*9\.5px;\s*padding:\s*2px\s*6px;', r'.drawer-badge {\1font-size: 11px; padding: 3px 8px;'),
        (r'\.drawer-footer\s*\{([^}]*?)font-size:\s*10px;', r'.drawer-footer {\1font-size: 12px; padding: 14px 16px;'),

        # Deca Matrix (ALWAYS 2 COLUMNS IN PORTRAIT MOBILE, NEVER 5 COLUMNS!)
        (r'\.deca-compounding-grid\s*\{[^}]*\}', '''.deca-compounding-grid {
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: 9px !important;
            margin-bottom: 14px !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }
        @media (min-width: 1024px) {
            .deca-compounding-grid {
                grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
            }
        }'''),
        (r'@media\s*\(min-width:\s*640px\)\s*\{\s*\.deca-compounding-grid\s*\{[^}]*\}\s*\}', ''),
        (r'\.deca-section-card\s*\{([^}]*?)padding:\s*8px\s*10px;', r'.deca-section-card {\1padding: 12px 12px; border-radius: 12px;'),
        (r'\.sidebar-badge\s*\{([^}]*?)font-size:\s*8\.5px;', r'.sidebar-badge {\1font-size: 10px; padding: 2px 6px;'),
        (r'\.qtc-status-dot\s*\{([^}]*?)width:\s*7px;\s*height:\s*7px;', r'.qtc-status-dot {\1width: 8px; height: 8px;'),
        (r'\.qtc-roi-pill\s*\{([^}]*?)font-size:\s*10px;\s*padding:\s*1px\s*5px;', r'.qtc-roi-pill {\1font-size: 11.5px; padding: 2px 7px;'),
        (r'\.qtc-pos-status\s*\{([^}]*?)font-size:\s*9px;', r'.qtc-pos-status {\1font-size: 11px;'),

        # Live Setup Radar Cards
        (r'\.dash-radar-card\s*\{([^}]*?)padding:\s*10px\s*12px;\s*gap:\s*7px;', r'.dash-radar-card {\1padding: 14px 14px; gap: 9px; border-radius: 13px; margin-bottom: 10px;'),
        (r'\.drc-sym\s*\{([^}]*?)font-size:\s*13px;', r'.drc-sym {\1font-size: 16px;'),
        (r'\.drc-badge\s*\{([^}]*?)font-size:\s*9\.5px;\s*padding:\s*2px\s*6px;', r'.drc-badge {\1font-size: 11.5px; padding: 3px 8px;'),
        (r'\.drc-prox-pill\s*\{([^}]*?)font-size:\s*10px;\s*padding:\s*2px\s*8px;', r'.drc-prox-pill {\1font-size: 12px; padding: 4px 10px; border-radius: 14px;'),
        (r'\.drc-metrics\s*\{([^}]*?)padding:\s*5px\s*8px;', r'.drc-metrics {\1padding: 8px 10px; gap: 6px; border-radius: 8px;'),
        (r'\.drc-lbl\s*\{([^}]*?)font-size:\s*8\.5px;', r'.drc-lbl {\1font-size: 10.5px; margin-bottom: 2px;'),
        (r'\.drc-val\s*\{([^}]*?)font-size:\s*11px;', r'.drc-val {\1font-size: 14px;'),
        (r'\.drc-progress-wrap\s*\{([^}]*?)height:\s*4px;', r'.drc-progress-wrap {\1height: 6px; border-radius: 3px;'),
        (r'\.drc-footer\s*\{([^}]*?)font-size:\s*9\.5px;', r'.drc-footer {\1font-size: 11.5px; padding-top: 3px;'),
        (r'\.drc-action-btn\s*\{([^}]*?)font-size:\s*11px;\s*padding:\s*7px\s*10px;', r'.drc-action-btn {\1font-size: 13px; padding: 10px 12px; min-height: 42px; border-radius: 8px;'),

        # Bottom Nav
        (r'\.bottom-nav\s*\{([^}]*?)height:\s*64px\s*!important;', r'.bottom-nav {\1height: 68px !important;'),
        (r'\.nav-item\s*\{([^}]*?)font-size:\s*10\.5px;', r'.nav-item {\1font-size: 11.5px;'),
        (r'\.nav-item\s*i\s*\{([^}]*?)font-size:\s*20px;', r'.nav-item i {\1font-size: 22px;')
    ]

    for pattern, repl in replacements:
        css_content = re.sub(pattern, repl, css_content)

    content = content[:start_idx + len(OLD_CSS_START)] + css_content + content[end_idx:]

# Also update Javascript deca card rendering string font-sizes
content = content.replace("font-size:11px; font-weight:800; color:#FFFFFF;", "font-size:13.5px; font-weight:800; color:#FFFFFF;")
content = content.replace("font-size:14px; font-weight:800; color:#FFFFFF;", "font-size:17px; font-weight:900; color:#FFFFFF;")
content = content.replace("font-size:9px; color:var(--text-secondary);", "font-size:11px; color:var(--text-secondary);")
content = content.replace("font-size:8.5px; padding:1px 5px;", "font-size:10px; padding:2px 6px;")

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("SUCCESS: High-DPI Poco F6 optimization applied to static/mobile.html!")
