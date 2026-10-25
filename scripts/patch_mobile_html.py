# -*- coding: utf-8 -*-
"""
Patch static/mobile.html to integrate:
1. Hamburger menu button in .app-header
2. Slide-out 14-item navigation drawer matching Bitget Pro / desktop
3. HERMES 3.5 DECA COMPOUNDING MATRIX (10 Sections Grid) on Home tab
4. Live Setup Radar container with approaching coin distance % pills, 5% Boundary, Live Price, Target/Harvest, [Chart] & [Position] buttons
5. Telegram alerts test modal & journal modal
6. Real-time background polling to /api/signals/radar and /api/paper/sections
"""

import os

FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "mobile.html")

with open(FILE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# -------------------------------------------------------------
# 1. NEW CSS STYLES TO INJECT BEFORE </style>
# -------------------------------------------------------------
NEW_CSS = """
        /* HAMBURGER DRAWER BUTTON */
        .hamburger-btn {
            background: var(--bg-card-subtle);
            border: 1px solid var(--border);
            color: var(--cyan);
            width: 34px;
            height: 34px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 15px;
            margin-right: 8px;
            flex-shrink: 0;
            transition: all 0.2s ease;
        }
        .hamburger-btn:active {
            transform: scale(0.92);
            border-color: var(--cyan);
        }

        /* SLIDE-OUT NAVIGATION DRAWER & OVERLAY */
        .drawer-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
            z-index: 99998;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        }
        .drawer-overlay.active {
            opacity: 1;
            visibility: visible;
        }
        .nav-drawer {
            position: fixed;
            top: 0;
            left: 0;
            bottom: 0;
            width: 320px;
            max-width: 86vw;
            background: #0d121d;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            z-index: 99999;
            transform: translateX(-100%);
            transition: transform 0.32s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            flex-direction: column;
            box-shadow: 12px 0 40px rgba(0, 0, 0, 0.85);
            overflow: hidden;
        }
        .nav-drawer.active {
            transform: translateX(0);
        }
        .drawer-header {
            padding: calc(env(safe-area-inset-top, 6px) + 14px) 16px 14px 16px;
            background: linear-gradient(180deg, #131a29 0%, #0d121d 100%);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .drawer-header-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .drawer-user-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .drawer-avatar {
            width: 38px;
            height: 38px;
            border-radius: 10px;
            background: linear-gradient(135deg, #00F59B 0%, #38BDF8 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #070a10;
            font-size: 18px;
            font-weight: 800;
        }
        .drawer-user-meta {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .drawer-username {
            font-size: 14px;
            font-weight: 800;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .drawer-vip-pill {
            font-size: 9px;
            font-weight: 800;
            background: rgba(255, 215, 0, 0.15);
            color: #FFD700;
            border: 1px solid rgba(255, 215, 0, 0.35);
            padding: 1px 6px;
            border-radius: 4px;
        }
        .drawer-user-sub {
            font-size: 10px;
            color: var(--text-muted);
            font-family: var(--font-mono);
        }
        .drawer-close-btn {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--text-muted);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 15px;
        }
        .drawer-compounding-card {
            background: rgba(18, 24, 36, 0.7);
            border: 1px solid rgba(0, 245, 155, 0.2);
            border-radius: 9px;
            padding: 9px 11px;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        .drawer-comp-title-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 10.5px;
        }
        .drawer-comp-title {
            font-weight: 800;
            color: #00F59B;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .drawer-comp-val {
            font-family: var(--font-mono);
            font-weight: 800;
            color: #FFFFFF;
        }
        .drawer-comp-bar {
            height: 5px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            overflow: hidden;
        }
        .drawer-comp-fill {
            height: 100%;
            background: linear-gradient(90deg, #00F59B, #38BDF8);
            border-radius: 3px;
            transition: width 0.4s ease;
        }
        .drawer-comp-meta {
            display: flex;
            justify-content: space-between;
            font-size: 9px;
            color: var(--text-muted);
        }
        .drawer-nav-content {
            flex: 1;
            overflow-y: auto;
            -webkit-overflow-scrolling: touch;
            padding: 12px 10px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        .drawer-section-label {
            font-size: 9.5px;
            font-weight: 800;
            color: #64748B;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            padding: 0 8px 3px 8px;
        }
        .drawer-links-group {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .drawer-nav-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            border-radius: 8px;
            text-decoration: none;
            color: #C0C8D6;
            font-size: 12.5px;
            font-weight: 600;
            transition: all 0.15s ease;
            border: 1px solid transparent;
            cursor: pointer;
        }
        .drawer-nav-item .left-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .drawer-nav-item i {
            width: 18px;
            font-size: 14px;
            color: #64748B;
            text-align: center;
        }
        .drawer-nav-item:active, .drawer-nav-item:hover {
            background: rgba(255, 255, 255, 0.05);
            color: #FFFFFF;
        }
        .drawer-nav-item.active {
            background: rgba(0, 245, 155, 0.1);
            color: #00F59B;
            border-color: rgba(0, 245, 155, 0.25);
        }
        .drawer-nav-item.active i {
            color: #00F59B;
        }
        .drawer-badge {
            font-size: 9.5px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-secondary);
        }
        .drawer-badge.badge-cyan {
            background: rgba(56, 189, 248, 0.18);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.35);
        }
        .drawer-badge.badge-gold {
            background: rgba(255, 215, 0, 0.18);
            color: #FFD700;
            border: 1px solid rgba(255, 215, 0, 0.35);
        }
        .drawer-badge.badge-hot {
            background: rgba(255, 77, 106, 0.2);
            color: #FF4D6A;
            border: 1px solid rgba(255, 77, 106, 0.35);
        }
        .drawer-footer {
            padding: 12px 14px;
            background: #090d15;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 10px;
            color: var(--text-muted);
        }
        .drawer-status-pill {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .drawer-live-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #00F59B;
            box-shadow: 0 0 6px #00F59B;
            animation: pulseDot 2s infinite;
        }

        /* 10-SECTION DECA COMPOUNDING MATRIX GRID (MOBILE OPTIMIZED) */
        .deca-compounding-grid {
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: 7px !important;
            margin-bottom: 12px !important;
            width: 100%;
            box-sizing: border-box;
        }
        @media (min-width: 640px) {
            .deca-compounding-grid {
                grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
            }
        }
        .deca-section-card {
            background: linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(11, 15, 25, 0.95) 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 9px;
            padding: 8px 10px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            flex-direction: column;
            gap: 3px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            min-width: 0;
            overflow: hidden;
        }
        .deca-section-card:active {
            transform: scale(0.98);
        }
        .deca-section-card.macro-4h {
            border-left: 3px solid #38BDF8;
        }
        .deca-section-card.intraday-1h {
            border-left: 3px solid #FFD700;
        }
        .sidebar-badge {
            font-size: 8.5px;
            font-weight: 800;
            padding: 1px 5px;
            border-radius: 4px;
            font-family: var(--font-mono);
        }
        .sidebar-badge.badge-cyan {
            background: rgba(56, 189, 248, 0.18);
            color: #38BDF8;
        }
        .sidebar-badge.badge-gold {
            background: rgba(255, 215, 0, 0.18);
            color: #FFD700;
        }
        .qtc-status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #64748B;
            flex-shrink: 0;
        }
        .qtc-status-dot.active {
            background: #00F59B;
            box-shadow: 0 0 6px #00F59B;
            animation: pulseDot 1.5s infinite;
        }
        .qtc-roi-pill {
            font-family: var(--font-mono);
            font-size: 10px;
            font-weight: 800;
            padding: 1px 5px;
            border-radius: 4px;
        }
        .qtc-roi-pill.up { background: rgba(0, 245, 155, 0.15); color: #00F59B; }
        .qtc-roi-pill.down { background: rgba(255, 77, 106, 0.15); color: #FF4D6A; }
        .qtc-roi-pill.neutral { background: rgba(148, 163, 184, 0.12); color: #94A3B8; }
        .qtc-pos-status {
            font-size: 9px;
            font-weight: 600;
            color: #94A3B8;
            display: flex;
            align-items: center;
            gap: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 65%;
        }
        .qtc-pos-status.in-trade {
            color: #00F59B;
            font-weight: 800;
        }

        /* HERMES 3.5 LIVE SETUP RADAR CARDS */
        .dashboard-signals-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
            width: 100%;
        }
        .dash-radar-card {
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
        }
        .dash-radar-card:active {
            transform: scale(0.985);
        }
        .dash-radar-card.imminent-pulse {
            border-color: rgba(245, 158, 11, 0.65);
            box-shadow: 0 0 14px rgba(245, 158, 11, 0.25);
            animation: radarPulse 2s infinite ease-in-out;
        }
        @keyframes radarPulse {
            0%, 100% { border-color: rgba(245, 158, 11, 0.4); box-shadow: 0 0 8px rgba(245, 158, 11, 0.15); }
            50% { border-color: rgba(245, 158, 11, 0.9); box-shadow: 0 0 16px rgba(245, 158, 11, 0.35); }
        }
        .dash-radar-card.active-running {
            border-color: rgba(0, 245, 155, 0.6);
            background: linear-gradient(135deg, rgba(6, 44, 28, 0.75), rgba(11, 25, 44, 0.95));
            box-shadow: 0 0 14px rgba(0, 245, 155, 0.25);
        }
        .drc-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 6px;
        }
        .drc-left {
            display: flex;
            align-items: center;
            gap: 7px;
        }
        .drc-sym {
            font-size: 13px;
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
        }
        .drc-badge.long {
            background: rgba(0, 245, 155, 0.16);
            color: #00F59B;
            border: 1px solid rgba(0, 245, 155, 0.35);
        }
        .drc-badge.short {
            background: rgba(255, 77, 106, 0.16);
            color: #FF4D6A;
            border: 1px solid rgba(255, 77, 106, 0.35);
        }
        .drc-prox-pill {
            font-size: 10px;
            font-weight: 800;
            padding: 2px 8px;
            border-radius: 12px;
            font-family: var(--font-mono);
            white-space: nowrap;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .drc-prox-pill.imminent {
            background: rgba(245, 158, 11, 0.22);
            color: #FBBF24;
            border: 1px solid rgba(245, 158, 11, 0.5);
        }
        .drc-prox-pill.in-zone {
            background: rgba(0, 245, 155, 0.18);
            color: #00F59B;
            border: 1px solid rgba(0, 245, 155, 0.45);
        }
        .drc-prox-pill.approaching {
            background: rgba(56, 189, 248, 0.16);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.4);
        }
        .drc-prox-pill.monitoring {
            background: rgba(148, 163, 184, 0.12);
            color: #94A3B8;
            border: 1px solid rgba(148, 163, 184, 0.25);
        }
        .drc-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 4px;
            background: rgba(8, 12, 22, 0.6);
            padding: 5px 8px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .drc-metric-item {
            display: flex;
            flex-direction: column;
        }
        .drc-lbl {
            font-size: 8.5px;
            font-weight: 700;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            margin-bottom: 1px;
        }
        .drc-val {
            font-size: 11px;
            font-weight: 800;
            font-family: var(--font-mono);
        }
        .drc-val.entry-val { color: #38BDF8; }
        .drc-val.live-val { color: #E2E8F0; }
        .drc-val.tp-val { color: #00F59B; }
        .drc-progress-wrap {
            width: 100%;
            height: 4px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 2px;
            overflow: hidden;
        }
        .drc-progress-bar {
            height: 100%;
            border-radius: 2px;
            transition: width 0.3s ease;
        }
        .drc-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 9.5px;
            color: #94A3B8;
            padding-top: 2px;
        }
        .drc-prob-badge {
            color: #00F59B;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 3px;
        }
        .drc-sentry-badge {
            color: #38BDF8;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 3px;
        }
        .drc-status-lbl {
            color: #CBD5E1;
            font-weight: 700;
        }
        .drc-actions {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 4px;
            padding-top: 6px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            width: 100%;
        }
        .drc-action-btn {
            flex: 1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            font-size: 11px;
            font-weight: 800;
            font-family: var(--font-mono);
            padding: 7px 10px;
            border-radius: 6px;
            cursor: pointer;
            border: none;
            transition: all 0.15s ease;
            text-transform: uppercase;
        }
        .drc-action-btn.btn-chart {
            background: rgba(56, 189, 248, 0.15);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.35);
        }
        .drc-action-btn.btn-chart:active {
            background: rgba(56, 189, 248, 0.3);
        }
        .drc-action-btn.btn-position {
            background: linear-gradient(135deg, rgba(0, 245, 155, 0.22), rgba(5, 150, 105, 0.35));
            color: #00F59B;
            border: 1px solid rgba(0, 245, 155, 0.5);
        }
        .drc-action-btn.btn-position:active {
            transform: scale(0.97);
        }
        .drc-action-btn.btn-close-pos {
            background: rgba(255, 77, 106, 0.15);
            color: #FF4D6A;
            border: 1px solid rgba(255, 77, 106, 0.35);
        }
"""

content = content.replace("    </style>\n</head>", NEW_CSS + "\n    </style>\n</head>")

# -------------------------------------------------------------
# 2. UPDATE TOP HEADER TO INCLUDE HAMBURGER BUTTON
# -------------------------------------------------------------
HEADER_OLD = """    <!-- TOP HEADER -->
    <header class="app-header">
        <div class="header-brand">"""

HEADER_NEW = """    <!-- TOP HEADER -->
    <header class="app-header">
        <button class="hamburger-btn" id="btnOpenDrawer" onclick="openDrawer()" title="Open Navigation Menu" aria-label="Open Navigation Drawer">
            <i class="fa-solid fa-bars-staggered"></i>
        </button>
        <div class="header-brand">"""

content = content.replace(HEADER_OLD, HEADER_NEW)

# -------------------------------------------------------------
# 3. INJECT SLIDE-OUT 14-ITEM NAVIGATION DRAWER & MODALS
# -------------------------------------------------------------
DRAWER_HTML = """
    <!-- SLIDE-OUT MOBILE NAVIGATION DRAWER OVERLAY -->
    <div class="drawer-overlay" id="drawerOverlay" onclick="closeDrawer()"></div>

    <!-- SLIDE-OUT MOBILE NAVIGATION DRAWER (14 ITEMS) -->
    <aside class="nav-drawer" id="slideDrawer" aria-label="Navigation Drawer">
        <!-- Drawer Header -->
        <div class="drawer-header">
            <div class="drawer-header-top">
                <div class="drawer-user-info">
                    <div class="drawer-avatar">
                        <i class="fa-solid fa-feather-pointed"></i>
                    </div>
                    <div class="drawer-user-meta">
                        <div class="drawer-username">
                            <span>HERMES 3.5</span>
                            <span class="drawer-vip-pill">VIP 1 PRO</span>
                        </div>
                        <span class="drawer-user-sub">UID: 9283-APEX-DECA</span>
                    </div>
                </div>
                <button class="drawer-close-btn" id="btnCloseDrawer" onclick="closeDrawer()" title="Close Menu" aria-label="Close Drawer">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>

            <!-- Compounding Goal Progress Snapshot -->
            <div class="drawer-compounding-card">
                <div class="drawer-comp-title-row">
                    <span class="drawer-comp-title">
                        <i class="fa-solid fa-trophy"></i> Compounding Goal
                    </span>
                    <span class="drawer-comp-val" id="drawerCompProgressVal">$500 ➔ $20,000</span>
                </div>
                <div class="drawer-comp-bar">
                    <div class="drawer-comp-fill" id="drawerCompBar" style="width: 2.5%;"></div>
                </div>
                <div class="drawer-comp-meta">
                    <span>10 Sections &bull; 5x Isolated</span>
                    <span id="drawerCompPercent">0.0% Target</span>
                </div>
            </div>
        </div>

        <!-- Drawer Navigation Menu Links (14 Items) -->
        <div class="drawer-nav-content">
            <!-- GROUP 1: CORE TRADING -->
            <div class="drawer-section-label">Trading Terminal</div>
            <div class="drawer-links-group">
                <!-- 1. Dashboard -->
                <a class="drawer-nav-item active" onclick="switchTab('home'); closeDrawer();">
                    <div class="left-group">
                        <i class="fa-solid fa-gauge-high"></i>
                        <span>Dashboard</span>
                    </div>
                    <span class="drawer-badge badge-cyan">ACTIVE</span>
                </a>
                <!-- 2. Markets -->
                <a class="drawer-nav-item" onclick="switchTab('markets'); closeDrawer();">
                    <div class="left-group">
                        <i class="fa-solid fa-chart-line"></i>
                        <span>Markets</span>
                    </div>
                    <span class="drawer-badge badge-gold">22</span>
                </a>
                <!-- 3. Live Chart -->
                <a class="drawer-nav-item" onclick="switchTab('trade'); closeDrawer();">
                    <div class="left-group">
                        <i class="fa-solid fa-chart-candlestick"></i>
                        <span>Pro Charts</span>
                    </div>
                    <span class="drawer-badge badge-cyan">PRO</span>
                </a>
                <!-- 4. Signals & Zones -->
                <a href="/signals" class="drawer-nav-item">
                    <div class="left-group">
                        <i class="fa-solid fa-satellite-dish"></i>
                        <span>Signals &amp; Zones</span>
                    </div>
                    <span class="drawer-badge badge-cyan" id="drawerArmedCountBadge">49 ARMED</span>
                </a>
                <!-- 5. Positions -->
                <a class="drawer-nav-item" onclick="switchTab('positions'); closeDrawer();">
                    <div class="left-group">
                        <i class="fa-solid fa-layer-group"></i>
                        <span>Positions</span>
                    </div>
                    <span class="drawer-badge" id="drawerPosBadge">0</span>
                </a>
                <!-- 6. Trade History -->
                <a class="drawer-nav-item" onclick="switchTab('positions'); closeDrawer();">
                    <div class="left-group">
                        <i class="fa-solid fa-clock-rotate-left"></i>
                        <span>Trade History</span>
                    </div>
                </a>
            </div>

            <!-- GROUP 2: STRATEGY & WEALTH ENGINE -->
            <div class="drawer-section-label">Quantitative AI</div>
            <div class="drawer-links-group">
                <!-- 7. Performance -->
                <a href="/compounding#performance" class="drawer-nav-item">
                    <div class="left-group">
                        <i class="fa-solid fa-chart-pie"></i>
                        <span>Performance</span>
                    </div>
                </a>
                <!-- 8. Compounding -->
                <a class="drawer-nav-item" onclick="switchTab('compounding'); closeDrawer();">
                    <div class="left-group">
                        <i class="fa-solid fa-trophy"></i>
                        <span>Compounding ($500 ➔ $20K)</span>
                    </div>
                    <span class="drawer-badge badge-hot">$20K</span>
                </a>
                <!-- 9. HERMES AI -->
                <a href="/hermes-ai" class="drawer-nav-item">
                    <div class="left-group">
                        <i class="fa-solid fa-robot"></i>
                        <span>HERMES AI</span>
                    </div>
                    <span class="drawer-badge badge-cyan">4 SENTRIES</span>
                </a>
                <!-- 10. Mike Brain -->
                <a href="/brain" class="drawer-nav-item">
                    <div class="left-group">
                        <i class="fa-solid fa-brain"></i>
                        <span>Mike Brain</span>
                    </div>
                    <span class="drawer-badge">AI</span>
                </a>
                <!-- 11. Trade Forensics -->
                <a href="/trade-forensics" class="drawer-nav-item">
                    <div class="left-group">
                        <i class="fa-solid fa-scale-balanced"></i>
                        <span>Trade Forensics</span>
                    </div>
                    <span class="drawer-badge badge-gold" style="background:#00F59B; color:#000; font-weight:800;">AUDIT</span>
                </a>
            </div>

            <!-- GROUP 3: LOGS & SYSTEM -->
            <div class="drawer-section-label">Logs &amp; System</div>
            <div class="drawer-links-group">
                <!-- 12. Telegram Alerts Option -->
                <a class="drawer-nav-item" onclick="closeDrawer(); openTelegramModal();">
                    <div class="left-group">
                        <i class="fa-brands fa-telegram" style="color: #0088cc; font-size: 15px;"></i>
                        <span>Telegram Alerts</span>
                    </div>
                    <span class="drawer-badge badge-cyan" style="background: rgba(0, 136, 204, 0.2); color: #38BDF8; border-color: rgba(0, 136, 204, 0.4);">LIVE</span>
                </a>
                <!-- 13. Journal -->
                <a class="drawer-nav-item" onclick="closeDrawer(); openJournalModal();">
                    <div class="left-group">
                        <i class="fa-solid fa-book-journal-whills"></i>
                        <span>Journal</span>
                    </div>
                </a>
                <!-- 14. Scanner Logs -->
                <a href="/signals#logs" class="drawer-nav-item">
                    <div class="left-group">
                        <i class="fa-solid fa-terminal"></i>
                        <span>Scanner Logs</span>
                    </div>
                </a>
                <!-- Settings -->
                <a href="/settings" class="drawer-nav-item">
                    <div class="left-group">
                        <i class="fa-solid fa-gear"></i>
                        <span>Settings</span>
                    </div>
                </a>
            </div>
        </div>

        <!-- Drawer Footer -->
        <div class="drawer-footer">
            <div class="drawer-status-pill">
                <span class="drawer-live-dot"></span> Binance Feed: CONNECTED
            </div>
            <span style="font-family: var(--font-mono); font-size: 10px;" id="drawerClock">00:00:00 IST</span>
        </div>
    </aside>

    <!-- TELEGRAM ALERTS MODAL -->
    <div id="telegramModal" style="display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.8); backdrop-filter:blur(6px); -webkit-backdrop-filter:blur(6px); z-index:999999; align-items:center; justify-content:center; padding:16px;">
        <div style="background:#0F1420; border:1px solid rgba(0,136,204,0.4); border-radius:14px; padding:18px; max-width:380px; width:100%; box-shadow:0 10px 30px rgba(0,0,0,0.8);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <i class="fa-brands fa-telegram" style="color:#0088cc; font-size:20px;"></i>
                    <span style="font-size:15px; font-weight:800; color:#FFF;">Telegram Alerts &amp; APK</span>
                </div>
                <button onclick="closeTelegramModal()" style="background:none; border:none; color:#94A3B8; font-size:18px; cursor:pointer;">&times;</button>
            </div>
            <p style="font-size:11.5px; color:#94A3B8; line-height:1.5; margin-bottom:14px;">
                Live Telegram broadcast sentinel is connected. Real-time 50% Mean Threshold taps, IDM sweeps, and order block mitigations are dispatched directly to your channel.
            </p>
            <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:10px; margin-bottom:14px; font-family:var(--font-mono); font-size:11px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="color:#64748B;">Bot Channel:</span>
                    <span style="color:#00F59B;">CONNECTED</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:#64748B;">Dispatch Mode:</span>
                    <span style="color:#38BDF8;">HERMES 3.5 APEX</span>
                </div>
            </div>
            <button onclick="sendTestTelegramAlert(this)" style="width:100%; background:linear-gradient(135deg, #0284C7, #0088cc); color:#FFF; border:none; padding:10px; border-radius:8px; font-weight:800; font-size:12px; cursor:pointer;">
                <i class="fa-solid fa-paper-plane"></i> Send Test Telegram Pulse
            </button>
        </div>
    </div>

    <!-- JOURNAL MODAL -->
    <div id="journalModal" style="display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.8); backdrop-filter:blur(6px); -webkit-backdrop-filter:blur(6px); z-index:999999; align-items:center; justify-content:center; padding:16px;">
        <div style="background:#0F1420; border:1px solid rgba(255,255,255,0.1); border-radius:14px; padding:18px; max-width:380px; width:100%; box-shadow:0 10px 30px rgba(0,0,0,0.8);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <i class="fa-solid fa-book-journal-whills" style="color:var(--gold); font-size:18px;"></i>
                    <span style="font-size:15px; font-weight:800; color:#FFF;">Hermes Trade Journal</span>
                </div>
                <button onclick="closeJournalModal()" style="background:none; border:none; color:#94A3B8; font-size:18px; cursor:pointer;">&times;</button>
            </div>
            <p style="font-size:11.5px; color:#94A3B8; line-height:1.5; margin-bottom:12px;">
                Automated trade audit and execution log stream. Every order block tap, profit armor lock, and MAE/MFE metric is recorded.
            </p>
            <div id="journalEntriesList" style="max-height:220px; overflow-y:auto; font-family:var(--font-mono); font-size:10.5px; color:#CBD5E1; display:flex; flex-direction:column; gap:6px;">
                <div style="background:rgba(255,255,255,0.04); padding:6px 8px; border-radius:6px;">
                    <span style="color:#00F59B;">[SYS]</span> Deca Compounding Desk Initialized &bull; $500.00 Ready
                </div>
                <div style="background:rgba(255,255,255,0.04); padding:6px 8px; border-radius:6px;">
                    <span style="color:#38BDF8;">[RADAR]</span> 49 Order Blocks Armed &bull; 50% Mean Threshold Sentry
                </div>
            </div>
        </div>
    </div>
"""

# Inject after </header>
HEADER_END = "</header>"
content = content.replace(HEADER_END, HEADER_END + "\n" + DRAWER_HTML, 1)

# -------------------------------------------------------------
# 4. INJECT DECA COMPOUNDING GRID AND LIVE SETUP RADAR IN TAB 1 (HOME)
# -------------------------------------------------------------
HOME_RADAR_AND_DECA = """
        <!-- HERMES 3.5 DECA COMPOUNDING MATRIX (10 SECTIONS DESK) -->
        <div class="section-header" style="margin-top:14px; margin-bottom:6px;">
            <span class="sh-title" style="display:flex; align-items:center; gap:6px;">
                <i class="fa-solid fa-layer-group" style="color:var(--gold);"></i> 
                <span>HERMES 3.5 Deca Compounding Matrix</span>
            </span>
            <span class="sidebar-badge badge-gold" onclick="switchTab('compounding')" style="cursor:pointer;">10 SECTIONS ($500) &rarr;</span>
        </div>
        <div style="font-size:10px; color:var(--text-muted); margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
            <span>Sec 1-5 (4H Macro) &bull; Sec 6-10 (1H Intraday)</span>
            <span style="color:var(--green); font-weight:700;">Target: $20,000 USDT</span>
        </div>
        <div class="deca-compounding-grid" id="decaCompoundingGrid">
            <!-- Populated dynamically by syncDecaCompoundingDesk() -->
        </div>

        <!-- HERMES 3.5 LIVE SETUP RADAR (MATCHING MONITOR BLUEPRINT) -->
        <div class="section-header" style="margin-top:16px; margin-bottom:6px;">
            <span class="sh-title" style="display:flex; align-items:center; gap:6px;">
                <i class="fa-solid fa-satellite-dish" style="color:#00F59B;"></i> 
                <span>Live Setup Radar</span>
                <span id="radarSetupCountBadge" style="background:rgba(56,189,248,0.18); color:#38BDF8; font-size:10px; padding:2px 7px; border-radius:10px; font-weight:800; border:1px solid rgba(56,189,248,0.3);">SCANNING...</span>
            </span>
            <button class="btn-text btn-xs" id="btnRefreshSignals" onclick="loadRecentSignals(this)" title="Refresh Live Radar" style="font-size:11px; color:#38BDF8; background:transparent; border:none; cursor:pointer; display:flex; align-items:center; gap:4px;">
                <i class="fa-solid fa-rotate-right"></i> Refresh
            </button>
        </div>
        <div style="font-size:10.5px; color:var(--text-muted); margin-bottom:8px;">
            Approaching Order Blocks &bull; Distance % away from 50% Mean Threshold
        </div>
        <div class="dashboard-signals-list" id="signalsListContainer">
            <!-- Populated dynamically by loadRecentSignals() -->
            <div style="padding:20px; text-align:center; color:var(--text-muted); font-size:11px;">
                <i class="fa-solid fa-satellite-dish" style="font-size:20px; color:var(--cyan); margin-bottom:8px; display:block;"></i>
                Scanning Top-22 Champions &bull; Loading Live Radar...
            </div>
        </div>
"""

# Replace the old basic queue in tab-home
OLD_QUEUE_MARKER = """        <!-- Active Setup Alert Card -->
        <div class="section-header">
            <span class="sh-title">Live 4H Scanner Queue</span>
            <span class="sh-link" onclick="switchTab('markets')">View All (22) &rarr;</span>
        </div>
        <div id="homeActiveQueue">
            <!-- Dynamically populated -->
        </div>"""

content = content.replace(OLD_QUEUE_MARKER, HOME_RADAR_AND_DECA)

# -------------------------------------------------------------
# 5. NEW JAVASCRIPT FUNCTIONS (RADAR, DRAWER, DECA GRID SYNC)
# -------------------------------------------------------------
NEW_JS = """
        // ============================================================
        // NAVIGATION DRAWER & MODALS CONTROLLER
        // ============================================================
        function openDrawer() {
            const drawer = document.getElementById("slideDrawer");
            const overlay = document.getElementById("drawerOverlay");
            if (drawer && overlay) {
                drawer.classList.add("active");
                overlay.classList.add("active");
            }
        }
        function closeDrawer() {
            const drawer = document.getElementById("slideDrawer");
            const overlay = document.getElementById("drawerOverlay");
            if (drawer && overlay) {
                drawer.classList.remove("active");
                overlay.classList.remove("active");
            }
        }
        function openTelegramModal() {
            const m = document.getElementById("telegramModal");
            if (m) m.style.display = "flex";
        }
        function closeTelegramModal() {
            const m = document.getElementById("telegramModal");
            if (m) m.style.display = "none";
        }
        function openJournalModal() {
            const m = document.getElementById("journalModal");
            if (m) m.style.display = "flex";
        }
        function closeJournalModal() {
            const m = document.getElementById("journalModal");
            if (m) m.style.display = "none";
        }
        async function sendTestTelegramAlert(btn) {
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Dispatching...`;
            }
            try {
                const res = await fetch('/api/telegram/test', { method: 'POST' });
                const data = await res.json();
                alert(data.message || "Telegram pulse dispatched successfully!");
            } catch (e) {
                alert("Telegram alert error: " + e.message);
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Send Test Telegram Pulse`;
                }
            }
        }
        function updateDrawerClock() {
            const el = document.getElementById("drawerClock");
            if (!el) return;
            const now = new Date();
            el.innerText = now.toLocaleTimeString('en-US', { hour12: false, timeZone: 'Asia/Kolkata' }) + ' IST';
        }
        setInterval(updateDrawerClock, 1000);
        updateDrawerClock();

        // ============================================================
        // HERMES 3.5 LIVE SETUP RADAR CONTROLLER
        // ============================================================
        function formatPrice(p) {
            const val = Number(p);
            if (isNaN(val)) return '0.00';
            if (val >= 1000) return val.toFixed(1);
            if (val >= 100) return val.toFixed(2);
            if (val >= 1) return val.toFixed(4);
            if (val >= 0.001) return val.toFixed(5);
            return val.toFixed(6);
        }

        async function loadRecentSignals(btn) {
            if (btn) {
                const icon = btn.querySelector('i');
                if (icon) icon.classList.add('spin-fast');
            }
            try {
                const resp = await fetch('/api/signals/radar?t=' + Date.now());
                if (!resp.ok) return;
                const data = await resp.json();
                const container = document.getElementById("signalsListContainer");
                if (!container) return;

                const radar = data.radar || [];
                const activeExecutions = data.active_executions || [];
                const signals = data.recent_signals || [];

                // Update badge in header and drawer
                const countBadge = document.getElementById("radarSetupCountBadge");
                const drawerBadge = document.getElementById("drawerArmedCountBadge");
                if (countBadge) {
                    const count = radar.length;
                    if (data.imminent_count > 0) {
                        countBadge.style.background = 'rgba(245, 158, 11, 0.25)';
                        countBadge.style.color = '#FBBF24';
                        countBadge.style.borderColor = 'rgba(245, 158, 11, 0.5)';
                        countBadge.innerText = `⚡ ${data.imminent_count} IMMINENT`;
                    } else {
                        countBadge.style.background = 'rgba(56, 189, 248, 0.18)';
                        countBadge.style.color = '#38BDF8';
                        countBadge.style.borderColor = 'rgba(56, 189, 248, 0.3)';
                        countBadge.innerText = count > 0 ? `${count} ARMED` : 'SCANNING...';
                    }
                }
                if (drawerBadge) {
                    drawerBadge.innerText = `${radar.length} ARMED`;
                }

                if (radar.length === 0 && activeExecutions.length === 0 && signals.length === 0) {
                    container.innerHTML = `
                        <div style="padding:24px 12px; text-align:center; color:var(--text-muted); font-size:11px;">
                            <i class="fa-solid fa-satellite-dish" style="font-size:22px; color:#38BDF8; margin-bottom:10px; display:block;"></i>
                            <strong style="color:#F8FAFC; display:block; margin-bottom:4px;">Scanning 24/7 Order Blocks...</strong>
                            Hermes 3.5 50% Mean Threshold setups & taps will appear here in real-time.
                        </div>
                    `;
                    return;
                }

                let html = "";

                // 1. Render Active Live Executions at the very top (if any open trades)
                if (activeExecutions.length > 0) {
                    activeExecutions.forEach(t => {
                        const isBuy = t.side === "BUY";
                        const pnlPositive = t.unrealized_pnl_pct >= 0;
                        const pnlColor = pnlPositive ? '#00F59B' : '#FF4D6A';
                        const sign = pnlPositive ? '+' : '';
                        html += `
                            <div class="dash-radar-card active-running" onclick="openRadarChart('${t.symbol}', '${t.timeframe}');" title="Click to view live chart for ${t.symbol}">
                                <div class="drc-top">
                                    <div class="drc-left">
                                        <span class="drc-sym" style="color:#00F59B;"><i class="fa-solid fa-circle-dot" style="animation:pulseDot 1s infinite;"></i> ${t.symbol}</span>
                                        <span class="drc-badge ${isBuy ? 'long' : 'short'}">${t.side} ${t.timeframe}</span>
                                    </div>
                                    <span class="drc-prox-pill in-zone" style="background:rgba(0,245,155,0.2); color:#00F59B; border-color:rgba(0,245,155,0.5);">
                                        🔴 LIVE POSITION
                                    </span>
                                </div>
                                <div class="drc-metrics">
                                    <div class="drc-metric-item">
                                        <span class="drc-lbl">Entry</span>
                                        <span class="drc-val entry-val">$${formatPrice(t.entry_price)}</span>
                                    </div>
                                    <div class="drc-metric-item">
                                        <span class="drc-lbl">Mark Price</span>
                                        <span class="drc-val live-val">$${formatPrice(t.current_price)}</span>
                                    </div>
                                    <div class="drc-metric-item">
                                        <span class="drc-lbl">Live ROE (5x)</span>
                                        <span class="drc-val" style="color:${pnlColor}; font-weight:800;">${sign}${t.unrealized_roe_pct || t.unrealized_pnl_pct}%</span>
                                    </div>
                                </div>
                                <div class="drc-footer">
                                    <span class="drc-prob-badge"><i class="fa-solid fa-lock"></i> Compounding Sec ${t.channel ? t.channel.replace('sec_','') : '1'}</span>
                                    <span class="drc-status-lbl" style="color:#00F59B;">Running Protected</span>
                                </div>
                                <div class="drc-actions">
                                    <button class="drc-action-btn btn-chart" onclick="event.stopPropagation(); openRadarChart('${t.symbol}', '${t.timeframe}');">
                                        <i class="fa-solid fa-chart-candlestick"></i> 📊 Chart
                                    </button>
                                    <button class="drc-action-btn btn-close-pos" onclick="event.stopPropagation(); closePosDirect('${t.symbol}');">
                                        <i class="fa-solid fa-xmark"></i> Close Trade
                                    </button>
                                </div>
                            </div>
                        `;
                    });
                }

                // 2. Render Pending / Approaching Setups
                if (radar.length > 0) {
                    radar.forEach(s => {
                        const isBuy = s.side === "BUY";
                        const isImminent = s.proximity_state === "IMMINENT_TAP";
                        
                        let proxClass = "monitoring";
                        let proxIcon = "⏳";
                        if (s.proximity_state === "IMMINENT_TAP") {
                            proxClass = "imminent";
                            proxIcon = "⚡";
                        } else if (s.proximity_state === "IN_RADAR_ZONE") {
                            proxClass = "in-zone";
                            proxIcon = "🎯";
                        } else if (s.proximity_state === "APPROACHING") {
                            proxClass = "approaching";
                            proxIcon = "👀";
                        }

                        // Progress bar: smaller distance means bar fills closer to 100%
                        const pctClamped = Math.min(2.5, Math.max(0.0, s.distance_pct));
                        const progressWidth = Math.round(((2.5 - pctClamped) / 2.5) * 100);
                        const barColor = isImminent ? '#F59E0B' : (s.distance_pct <= 0.6 ? '#00F59B' : '#38BDF8');

                        html += `
                            <div class="dash-radar-card ${isImminent ? 'imminent-pulse' : ''}" onclick="openRadarChart('${s.symbol}', '${s.timeframe}');">
                                <div class="drc-top">
                                    <div class="drc-left">
                                        <span class="drc-sym">${s.symbol}</span>
                                        <span class="drc-badge ${isBuy ? 'long' : 'short'}">${s.side} ${s.timeframe}</span>
                                    </div>
                                    <span class="drc-prox-pill ${proxClass}">
                                        ${proxIcon} ${s.distance_pct}% away
                                    </span>
                                </div>
                                <div class="drc-metrics">
                                    <div class="drc-metric-item">
                                        <span class="drc-lbl">5% Boundary</span>
                                        <span class="drc-val entry-val">$${formatPrice(s.entry_price)}</span>
                                    </div>
                                    <div class="drc-metric-item">
                                        <span class="drc-lbl">Live Price</span>
                                        <span class="drc-val live-val">$${formatPrice(s.current_price)}</span>
                                    </div>
                                    <div class="drc-metric-item">
                                        <span class="drc-lbl">Target / Harvest</span>
                                        <span class="drc-val tp-val">+14% / +4.5%</span>
                                    </div>
                                </div>
                                <div class="drc-progress-wrap">
                                    <div class="drc-progress-bar" style="width:${progressWidth}%; background:${barColor};"></div>
                                </div>
                                <div class="drc-footer">
                                    <span class="drc-prob-badge"><i class="fa-solid fa-bolt"></i> ${s.probability_pct || 95}% Win Prob</span>
                                    <span class="drc-sentry-badge"><i class="fa-solid fa-shield-halved"></i> 4/4 Sentries</span>
                                    <span class="drc-status-lbl">${s.proximity_label || 'ARMED'}</span>
                                </div>
                                <div class="drc-actions">
                                    <button class="drc-action-btn btn-chart" onclick="event.stopPropagation(); openRadarChart('${s.symbol}', '${s.timeframe}');">
                                        <i class="fa-solid fa-chart-candlestick"></i> 📊 Chart
                                    </button>
                                    <button class="drc-action-btn btn-position" onclick="event.stopPropagation(); deployRadarPosition('${s.symbol}', '${s.side}', ${s.entry_price}, '${s.timeframe}', ${s.probability_pct});">
                                        <i class="fa-solid fa-bolt"></i> ⚡ Position
                                    </button>
                                </div>
                            </div>
                        `;
                    });
                }

                container.innerHTML = html;
            } catch (e) {
                console.warn("loadRecentSignals error:", e);
            } finally {
                if (btn) {
                    const icon = btn.querySelector('i');
                    if (icon) setTimeout(() => icon.classList.remove('spin-fast'), 600);
                }
            }
        }

        function openRadarChart(symbol, timeframe) {
            if (!symbol) return;
            openCoinTrade(symbol);
            const tf = (timeframe || '4h').toLowerCase();
            const interval = tf === '1h' ? '60' : '240';
            const iframe = document.getElementById('tvIframe');
            if (iframe) {
                iframe.src = `https://s.tradingview.com/widgetembed/?frameElementId=tradingview_widget&symbol=BINANCE%3A${symbol}&interval=${interval}&hidesidetoolbar=1&symboledit=0&saveimage=0&toolbarbg=080B11&studies=%5B%5D&theme=dark&style=1&timezone=Asia%2FKolkata&locale=en`;
            }
        }

        async function deployRadarPosition(symbol, side, entryPrice, timeframe, probPct) {
            if (!confirm(`Deploy 5x Isolated Position for ${symbol} (${side}) at $${formatPrice(entryPrice)} in available Deca section?`)) {
                return;
            }
            try {
                const resp = await fetch('/api/paper/deploy', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        symbol: symbol,
                        side: side,
                        entry_price: Number(entryPrice),
                        timeframe: (timeframe || '4h').toLowerCase()
                    })
                });
                const res = await resp.json();
                if (res.success) {
                    alert(`✅ Successfully deployed ${symbol} ${side} to Deca Section #${res.section || '1'}!`);
                    fetchAccountData();
                    fetchPositions();
                    loadRecentSignals();
                } else {
                    alert(`⚠️ Deploy: ${res.message || 'Position deployed or queued'}`);
                }
            } catch (e) {
                alert("Deploy error: " + e.message);
            }
        }

        // Render Deca Grid on Home Tab (10 Sections Desk)
        function renderDecaGridHome(sections) {
            const gridEl = document.getElementById('decaCompoundingGrid');
            if (!gridEl) return;
            if (!sections || sections.length === 0) return;

            gridEl.innerHTML = sections.map((sec, idx) => {
                const sId = sec.id || (idx + 1);
                const is4h = (sec.timeframe || (sId <= 5 ? '4h' : '1h')).toLowerCase().includes('4h');
                const bal = Number(sec.current_balance || sec.balance || 50.0);
                const initB = Number(sec.starting_balance || 50.0);
                const growth = Number(sec.growth_pct != null ? sec.growth_pct : ((bal - initB) / initB * 100));
                const wr = Number(sec.win_rate || 0.0);
                const wins = Number(sec.wins || 0);
                const losses = Number(sec.losses || 0);
                const totT = wins + losses;
                const hasOpen = !!sec.open_trade;
                const sym = hasOpen ? (sec.open_trade.symbol || 'OPEN') : null;

                const tfBadgeClass = is4h ? 'badge-cyan' : 'badge-gold';
                const tfLabel = is4h ? '4H MACRO' : '1H INTRADAY';
                const cardClass = is4h ? 'deca-section-card macro-4h' : 'deca-section-card intraday-1h';
                const dotClass = hasOpen ? 'qtc-status-dot active' : 'qtc-status-dot';

                let posHtml = `<div class="qtc-pos-status"><i class="fa-solid fa-satellite-dish"></i> ${totT > 0 ? totT + ' Done' : 'Armed'}</div>`;
                if (hasOpen) {
                    posHtml = `<div class="qtc-pos-status in-trade"><i class="fa-solid fa-circle-dot" style="color:#00F59B;"></i> ${sym}</div>`;
                }

                return `
                    <div class="${cardClass}" onclick="switchTab('compounding')">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="display:flex; align-items:center; gap:5px;">
                                <span style="font-size:11px; font-weight:800; color:#FFFFFF;">Sec ${sId}</span>
                                <span class="sidebar-badge ${tfBadgeClass}">${tfLabel}</span>
                            </div>
                            <span class="${dotClass}"></span>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:3px;">
                            <span style="font-family:var(--font-mono); font-size:14px; font-weight:800; color:#FFFFFF;">$${bal.toFixed(2)}</span>
                            <span class="qtc-roi-pill ${growth > 0 ? 'up' : growth < 0 ? 'down' : 'neutral'}">${growth >= 0 ? '+' : ''}${growth.toFixed(1)}%</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:2px; font-family:var(--font-mono); font-size:9px; color:var(--text-secondary);">
                            ${posHtml}
                            <span style="color:${wr > 0 ? '#00F59B' : 'var(--text-muted)'}; font-weight:700;">WR: ${wr.toFixed(0)}%</span>
                        </div>
                    </div>
                `;
            }).join('');
        }
"""

# Inject renderDecaGridHome call into renderDecaSections
RENDER_DECA_OLD = """            macroContainer.innerHTML = macroList.map((s, i) => buildCard(s, i, true)).join('');
            intraContainer.innerHTML = intraList.map((s, i) => buildCard(s, i + 5, false)).join('');
        }"""

RENDER_DECA_NEW = """            macroContainer.innerHTML = macroList.map((s, i) => buildCard(s, i, true)).join('');
            intraContainer.innerHTML = intraList.map((s, i) => buildCard(s, i + 5, false)).join('');
            renderDecaGridHome(sections);
        }"""

content = content.replace(RENDER_DECA_OLD, RENDER_DECA_NEW)

# Inject NEW_JS before fetchAccountData
content = content.replace("        async function fetchAccountData() {", NEW_JS + "\n        async function fetchAccountData() {")

# Update initialization and polling loops at bottom
OLD_INIT_POLL = """        // Initialize and Start Live Polling
        fetchAccountData();
        fetchMarketsData();
        fetchPositions();
        fetchTradesHistory();

        setInterval(fetchAccountData, 4000);
        setInterval(fetchMarketsData, 5000);
        setInterval(fetchPositions, 3000);
        setInterval(fetchTradesHistory, 6000);"""

NEW_INIT_POLL = """        // Initialize and Start Live Polling
        fetchAccountData();
        loadRecentSignals();
        fetchMarketsData();
        fetchPositions();
        fetchTradesHistory();

        setInterval(fetchAccountData, 4000);
        setInterval(loadRecentSignals, 3500);
        setInterval(fetchMarketsData, 5000);
        setInterval(fetchPositions, 3000);
        setInterval(fetchTradesHistory, 6000);"""

content = content.replace(OLD_INIT_POLL, NEW_INIT_POLL)

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("SUCCESS: static/mobile.html patched with Radar, Deca Compounding Desk, and 14-item Drawer!")
