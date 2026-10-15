import sys
from fastapi.testclient import TestClient
from app import app

def run_tests():
    print("==================================================")
    print("HERMES 3.5 HOLOGRAPHIC 2.0 TERMINAL VERIFICATION")
    print("==================================================")
    
    client = TestClient(app)
    
    endpoints = [
        "/hologram",
        "/nexus/hologram"
    ]
    
    for ep in endpoints:
        print(f"\n[TESTING ROUTE] {ep}...")
        resp = client.get(ep)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        # Verify headers
        cache_hdr = resp.headers.get("cache-control", "")
        print(f"  Status: {resp.status_code} OK")
        print(f"  Content-Type: {resp.headers.get('content-type')}")
        print(f"  Cache-Control: {cache_hdr}")
        assert "no-cache" in cache_hdr and "no-store" in cache_hdr, "Cache-Control missing no-cache/no-store"
        
        html = resp.text
        print(f"  Payload Size: {len(html)} bytes")
        
        # Verify Critical Specifications
        checks = [
            # Top Header & Emblem
            ("HERMES 3.5 SINGLE TIER", "Top Header Brand Emblem"),
            ("10-SECTION MATRIX LIVE", "10-Section Matrix Live Pill"),
            ("PWA & APK READY", "PWA/APK Banner"),
            ("HERMES_3.5_SINGLE_TIER_Trading_Terminal.apk", "APK Download Link"),
            ("notif-bell-btn", "Notification Bell Button"),
            ("hamburger-btn", "Drawer Hamburger Button"),
            
            # Hero Card - 3D Rotating Holographic Globe
            ("globeCanvas", "3D Globe HTML5 Canvas Element"),
            ("TOTAL EQUITY", "Total Equity Floating HUD"),
            ("$575.06", "Live Equity Initial Value"),
            ("+15.01% Return", "+15.01% Glowing Green Return Badge"),
            ("5x ISOLATED", "5x Isolated Badge"),
            ("Free Margin", "Free Margin Indicator"),
            ("Used Margin", "Used Margin Indicator"),
            ("HERMES 3.0 MODEL 2A", "Active Model 2A Badge"),
            ("$20,000.00 Target", "$20,000 Milestone Target"),
            ("progress-fill", "Deca Matrix Compounding Progress Bar"),
            
            # Live Ticker Tape (BTC & ETH prominently featured)
            ("BTCUSDT", "BTCUSDT Featured in Ticker Tape"),
            ("ETHUSDT", "ETHUSDT Featured in Ticker Tape"),
            ("tapeBtcPrice", "BTC Price Dynamic ID"),
            ("tapeEthPrice", "ETH Price Dynamic ID"),
            
            # 4-Sentries Diagnostic Matrix (Arc Reactor HUD)
            ("Sentry 1 - BTC Veto", "Sentry 1 Gauge"),
            ("NEUTRAL (Safe)", "Sentry 1 Status"),
            ("Sentry 2 - Displacement", "Sentry 2 Gauge"),
            ("&ge; 5.0% FVG", "Sentry 2 Status (>= 5.0% FVG)"),
            ("Sentry 3 - IDM Sweep", "Sentry 3 Gauge"),
            ("&ge; 18% Wick", "Sentry 3 Status (>= 18% Wick)"),
            ("Sentry 4 - Freshness", "Sentry 4 Gauge"),
            ("&le; 28 Bars", "Sentry 4 Status (<= 28 Bars)"),
            ("ARMED", "Armed Gauge Badges"),
            
            # Deca Compounding Matrix (10 Sections)
            ("DECA COMPOUNDING MATRIX", "10-Section Compounding Matrix Header"),
            ("Sec 1-5: 4H Macro", "4H Macro Strategy Descriptor"),
            ("Sec 6-10: 1H Intraday", "1H Intraday Strategy Descriptor"),
            ("decaSectionsContainer", "Dynamic 10-Section Rendering Container"),
            
            # Live Setup Radar Card
            ("INSTITUTIONAL 50% MT SETUP RADAR", "50% MT Radar Header"),
            ("setupsFeedList", "Radar Setups List Container"),
            ("btn-chart", "Chart Action Button"),
            ("btn-position", "Position Action Button"),
            
            # Bottom Navigation Dock
            ("bottom-nav-dock", "Bottom Dock Container"),
            ('href="/trade"', "Dock Tab: Futures/Home"),
            ('href="/nexus/markets"', "Dock Tab: Markets"),
            ("center-floating-sphere-btn", "Center 3D Floating Glowing Holographic Sphere"),
            ('href="/nexus/deca"', "Dock Tab: Compounding"),
            ('href="/trade#positions"', "Dock Tab: Positions"),
            
            # Slide-out Drawer Menu (All Links)
            ("drawer-menu", "Slide-out Drawer Menu"),
            ('href="/trade"', "Drawer: /trade"),
            ('href="/nexus/markets"', "Drawer: /nexus/markets"),
            ('href="/nexus/deca"', "Drawer: /nexus/deca"),
            ('href="/nexus/assets"', "Drawer: /nexus/assets"),
            ('href="/hologram"', "Drawer: /hologram"),
            ('href="/"', "Drawer: / (Classic)"),
            ('href="/signals"', "Drawer: /signals"),
            ('href="/positions"', "Drawer: /positions"),
            ('href="/compounding"', "Drawer: /compounding"),
            ('href="/hermes-ai"', "Drawer: /hermes-ai"),
            ('href="/trade-forensics"', "Drawer: /trade-forensics"),
        ]
        
        passed = 0
        for needle, label in checks:
            if needle in html:
                print(f"  [PASS] {label}")
                passed += 1
            else:
                print(f"  [FAIL] {label} (not found: {needle})")
                assert False, f"Check failed: {label}"
        
        print(f"\n>> All {passed}/{len(checks)} specification checks passed for {ep}!")

    # Check that APIs respond correctly
    print("\n[TESTING API ENDPOINTS REQUIRED BY HOLOGRAM]")
    apis = ["/api/deca/summary", "/api/deca/sections", "/api/deca/setups"]
    for api_ep in apis:
        resp = client.get(api_ep)
        print(f"  {api_ep}: Status {resp.status_code}")
        assert resp.status_code == 200, f"API {api_ep} returned {resp.status_code}"
    
    print("\n==================================================")
    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY WITH 0 ERRORS!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
