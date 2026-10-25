import re

file_path = "static/mobile.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Viewport tag to ensure full mobile scale
content = re.sub(
    r'<meta name="viewport"[^>]*>',
    '<meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=5.0, viewport-fit=cover">',
    content,
    count=1
)

# 2. Update html and body CSS base sizes
content = content.replace(
    """        html {
            width: 100%;
            height: 100%;
            max-width: 100vw;
            overflow-x: hidden;
            -webkit-text-size-adjust: 100%;
            box-sizing: border-box;
            background-color: var(--bg-base);
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-primary);
            font-family: var(--font-sans);
            font-size: 15px;
            line-height: 1.5;
            width: 100%;
            max-width: 100vw;
            overflow-x: hidden;
            position: relative;
            padding-bottom: 84px;
            user-select: none;
            -webkit-user-select: none;
            box-sizing: border-box;
        }""",
    """        html {
            width: 100%;
            height: 100%;
            max-width: 100vw;
            overflow-x: hidden;
            -webkit-text-size-adjust: 100%;
            text-size-adjust: 100%;
            box-sizing: border-box;
            background-color: var(--bg-base);
            font-size: 16px;
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-primary);
            font-family: var(--font-sans);
            font-size: 16px;
            line-height: 1.5;
            width: 100%;
            max-width: 100vw;
            overflow-x: hidden;
            position: relative;
            padding-bottom: 92px;
            user-select: none;
            -webkit-user-select: none;
            box-sizing: border-box;
            -webkit-font-smoothing: antialiased;
        }"""
)

# 3. Upgrade Hero Wallet Card styles to match Image 1
content = content.replace(
    """        .hw-label {
            font-size: 12px;
            color: var(--text-muted);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .hw-badge {
            background: rgba(56, 189, 248, 0.15);
            color: var(--cyan);
            font-size: 9.5px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: var(--font-mono);
        }

        .hw-balance-row {
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin-bottom: 10px;
        }

        .hw-balance {
            font-size: 30px;
            font-weight: 900;
            letter-spacing: -0.5px;
            font-family: var(--font-mono);
            color: #FFFFFF;
        }

        .hw-pnl-pill {
            font-size: 10.5px;
            font-weight: 800;
            font-family: var(--font-mono);
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(0, 245, 155, 0.15);
            color: var(--green);
        }

        .hw-metrics-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 6px;
            padding-top: 8px;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            margin-bottom: 10px;
            width: 100%;
        }

        .hw-metric-item {
            display: flex;
            flex-direction: column;
            min-width: 0;
            overflow: hidden;
        }

        .hw-m-label {
            font-size: 11px;
            color: var(--text-muted);
            font-weight: 600;
            margin-bottom: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .hw-m-val {
            font-size: 14px;
            font-weight: 800;
            font-family: var(--font-mono);
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }""",
    """        .hw-label {
            font-size: 13.5px;
            color: var(--text-muted);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .hw-badge {
            background: rgba(56, 189, 248, 0.18);
            color: var(--cyan);
            font-size: 11.5px;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 5px;
            font-family: var(--font-mono);
            border: 1px solid rgba(56, 189, 248, 0.35);
        }

        .hw-balance-row {
            display: flex;
            align-items: baseline;
            gap: 10px;
            margin-bottom: 12px;
            margin-top: 2px;
        }

        .hw-balance {
            font-size: 34px;
            font-weight: 900;
            letter-spacing: -0.5px;
            font-family: var(--font-mono);
            color: #FFFFFF;
        }

        .hw-pnl-pill {
            font-size: 12px;
            font-weight: 800;
            font-family: var(--font-mono);
            padding: 3px 8px;
            border-radius: 5px;
            background: rgba(0, 245, 155, 0.18);
            color: var(--green);
            border: 1px solid rgba(0, 245, 155, 0.3);
        }

        .hw-metrics-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 8px;
            padding-top: 10px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 12px;
            width: 100%;
        }

        .hw-metric-item {
            display: flex;
            flex-direction: column;
            min-width: 0;
            overflow: hidden;
        }

        .hw-m-label {
            font-size: 12.5px;
            color: var(--text-muted);
            font-weight: 700;
            margin-bottom: 3px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .hw-m-val {
            font-size: 15.5px;
            font-weight: 800;
            font-family: var(--font-mono);
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }"""
)

# 4. Upgrade Challenge Box & Ticker
content = content.replace(
    """        .cb-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .cb-title {
            color: var(--gold);
            display: flex;
            align-items: center;
            gap: 5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .cb-target {
            color: var(--text-muted);
            font-family: var(--font-mono);
            font-size: 11.5px;
            white-space: nowrap;
        }

        .cb-progress-bar-bg {
            height: 7px;
            border-radius: 3px;
            background: rgba(255, 255, 255, 0.08);
            overflow: hidden;
            position: relative;
        }""",
    """        .cb-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13.5px;
            font-weight: 700;
            margin-bottom: 6px;
        }

        .cb-title {
            color: var(--gold);
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13.5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .cb-target {
            color: var(--text-muted);
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 700;
            white-space: nowrap;
        }

        .cb-progress-bar-bg {
            height: 9px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.08);
            overflow: hidden;
            position: relative;
        }"""
)

# 5. Upgrade Ticker chips
content = content.replace(
    """        .ticker-chip {
            flex: 0 0 auto;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 9px;
            padding: 8px 12px; border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            box-sizing: border-box;
        }

        .tc-coin {
            font-weight: 800;
            font-size: 12.5px;
        }

        .tc-price {
            font-family: var(--font-mono);
            font-size: 12.5px;
            font-weight: 700;
            color: var(--text-secondary);
        }

        .tc-badge {
            font-size: 9.5px;
            font-weight: 800;
            font-family: var(--font-mono);
        }""",
    """        .ticker-chip {
            flex: 0 0 auto;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 11px;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            box-sizing: border-box;
        }

        .tc-coin {
            font-weight: 800;
            font-size: 14.5px;
        }

        .tc-price {
            font-family: var(--font-mono);
            font-size: 14.5px;
            font-weight: 700;
            color: var(--text-secondary);
        }

        .tc-badge {
            font-size: 11.5px;
            font-weight: 800;
            font-family: var(--font-mono);
            padding: 2px 6px;
            border-radius: 4px;
        }"""
)

# 6. Upgrade 4-Sentries Diagnostic Matrix
content = content.replace(
    """        /* SENTRY STATUS RADAR CARD */
        .radar-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 10px;
            position: relative;
            width: 100%;
            box-sizing: border-box;
            overflow: hidden;
        }

        .rc-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .rc-title {
            font-size: 13.5px;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 5px;
            color: #FFFFFF;
        }

        .rc-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 6px;
            width: 100%;
        }

        .rc-item {
            background: var(--bg-card-subtle);
            border-radius: 8px;
            padding: 10px 12px; border-radius: 9px;
            border: 1px solid rgba(255, 255, 255, 0.04);
            min-width: 0;
            overflow: hidden;
        }

        .rc-item-name {
            font-size: 11px; margin-bottom: 3px;
            color: var(--text-muted);
            font-weight: 700;
            margin-bottom: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .rc-item-val {
            font-size: 13px;
            font-weight: 800;
            font-family: var(--font-mono);
            display: flex;
            align-items: center;
            gap: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }""",
    """        /* SENTRY STATUS RADAR CARD */
        .radar-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 15px 16px;
            margin-bottom: 14px;
            position: relative;
            width: 100%;
            box-sizing: border-box;
            overflow: hidden;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
        }

        .rc-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .rc-title {
            font-size: 15.5px;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 6px;
            color: #FFFFFF;
        }

        .rc-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 8px;
            width: 100%;
        }

        .rc-item {
            background: var(--bg-card-subtle);
            border-radius: 10px;
            padding: 12px 14px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            min-width: 0;
            overflow: hidden;
        }

        .rc-item-name {
            font-size: 12.5px;
            color: var(--text-muted);
            font-weight: 700;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .rc-item-val {
            font-size: 15.5px;
            font-weight: 800;
            font-family: var(--font-mono);
            display: flex;
            align-items: center;
            gap: 5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }"""
)

# 7. Upgrade Live Setup Radar & Deca cards
content = content.replace(
    """        .dash-radar-card {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(11, 17, 32, 0.95));
            border: 1px solid rgba(56, 189, 248, 0.18);
            border-radius: 10px;
            padding: 10px 12px;
            display: flex;
            flex-direction: column;
            gap: 7px;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
        }""",
    """        .dash-radar-card {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(11, 17, 32, 0.95));
            border: 1px solid rgba(56, 189, 248, 0.2);
            border-radius: 13px;
            padding: 14px 15px;
            display: flex;
            flex-direction: column;
            gap: 9px;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        }"""
)

content = content.replace(
    """        .drc-sym {
            font-size: 16px;
            font-weight: 800;
            color: #F8FAFC;
            font-family: var(--font-mono);
        }
        .drc-badge {
            font-size: 9.5px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: var(--font-mono);
            letter-spacing: 0.3px;
        }""",
    """        .drc-sym {
            font-size: 17.5px;
            font-weight: 900;
            color: #F8FAFC;
            font-family: var(--font-mono);
        }
        .drc-badge {
            font-size: 11.5px;
            font-weight: 800;
            padding: 3px 7px;
            border-radius: 5px;
            font-family: var(--font-mono);
            letter-spacing: 0.3px;
        }"""
)

content = content.replace(
    """        .drc-prox-pill {
            font-size: 10px;
            font-weight: 800;
            padding: 2px 8px;
            border-radius: 12px;
            font-family: var(--font-mono);
            white-space: nowrap;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }""",
    """        .drc-prox-pill {
            font-size: 12px;
            font-weight: 800;
            padding: 3px 9px;
            border-radius: 12px;
            font-family: var(--font-mono);
            white-space: nowrap;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }"""
)

content = content.replace(
    """        .drc-lbl {
            font-size: 11px;
            font-weight: 700;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            margin-bottom: 2px;
        }
        .drc-val {
            font-size: 14px;
            font-weight: 800;
            font-family: var(--font-mono);
        }""",
    """        .drc-lbl {
            font-size: 12px;
            font-weight: 700;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            margin-bottom: 3px;
        }
        .drc-val {
            font-size: 15.5px;
            font-weight: 800;
            font-family: var(--font-mono);
        }"""
)

content = content.replace(
    """        .drc-action-btn {
            flex: 1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            font-size: 13.5px;
            font-weight: 800;
            font-family: var(--font-mono);
            padding: 11px 12px;
            min-height: 44px;
            border-radius: 9px;
            cursor: pointer;
            border: none;
            transition: all 0.15s ease;
            text-transform: uppercase;
        }""",
    """        .drc-action-btn {
            flex: 1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 7px;
            font-size: 14.5px;
            font-weight: 800;
            font-family: var(--font-mono);
            padding: 12px 14px;
            min-height: 46px;
            border-radius: 10px;
            cursor: pointer;
            border: none;
            transition: all 0.15s ease;
            text-transform: uppercase;
        }"""
)

# 8. Deca card inner updates
content = content.replace(
    """        .qtc-pos-status {
            font-size: 11px;
            font-weight: 600;
            color: #94A3B8;
            display: flex;
            align-items: center;
            gap: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 65%;
        }""",
    """        .qtc-pos-status {
            font-size: 12.5px;
            font-weight: 700;
            color: #94A3B8;
            display: flex;
            align-items: center;
            gap: 5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 65%;
        }"""
)

# 9. Bottom Navigation Bar height & icon sizes
content = content.replace(
    """        :root {
            --bg-base: #080B11;
            --bg-card: #0F1420;
            --bg-card-subtle: #141B2B;
            --bg-elevated: #1A2236;
            --border: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(0, 245, 155, 0.25);
            --text-primary: #FFFFFF;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --green: #00F59B;
            --green-glow: rgba(0, 245, 155, 0.15);
            --red: #FF4D6A;
            --red-glow: rgba(255, 77, 106, 0.15);
            --cyan: #38BDF8;
            --gold: #FFD700;
            --gold-glow: rgba(255, 215, 0, 0.15);
            --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
            --bottom-nav-height: 64px;
        }""",
    """        :root {
            --bg-base: #080B11;
            --bg-card: #0F1420;
            --bg-card-subtle: #141B2B;
            --bg-elevated: #1A2236;
            --border: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(0, 245, 155, 0.25);
            --text-primary: #FFFFFF;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --green: #00F59B;
            --green-glow: rgba(0, 245, 155, 0.15);
            --red: #FF4D6A;
            --red-glow: rgba(255, 77, 106, 0.15);
            --cyan: #38BDF8;
            --gold: #FFD700;
            --gold-glow: rgba(255, 215, 0, 0.15);
            --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
            --bottom-nav-height: 70px;
        }"""
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully upgraded mobile.html to Image 1 normal phone scale!")
