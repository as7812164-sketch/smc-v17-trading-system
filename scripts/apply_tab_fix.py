import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\static\mobile.html', 'r', encoding='utf-8') as f:
    text = f.read()

with open(r'C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\scripts\missing_styles.css', 'r', encoding='utf-8') as f:
    missing_css = f.read()

# 1. Insert missing styles right before BITGET PRO OFFICIAL MOBILE POSITION CARD
target_marker = "/* =========================================================\n           BITGET PRO OFFICIAL MOBILE POSITION CARD"
idx_target = text.find(target_marker)

if idx_target != -1:
    print(f"Inserting missing component CSS at index {idx_target}")
    text = text[:idx_target] + missing_css + "\n\n        " + text[idx_target:]
    print("Inserted missing styles successfully!")
else:
    print("Could not find target marker!")

# 2. Update switchTab function for rock-solid instant tab display
old_switch_tab = """        function switchTab(tabId) {
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));

            const targetPanel = document.getElementById(`tab-${tabId}`);
            if (targetPanel) targetPanel.classList.add('active');

            const navIndex = ['home', 'markets', 'trade', 'compounding', 'positions'].indexOf(tabId);
            if (navIndex !== -1) {
                document.querySelectorAll('.nav-item')[navIndex].classList.add('active');
            }
            
            if (tabId === 'trade') {
                if (window.HermesMobileChart) {
                    const currentSym = document.getElementById('tradeSymbol') ? document.getElementById('tradeSymbol').innerText : 'BTCUSDT';
                    setTimeout(() => {
                        HermesMobileChart.init('mobileChartCanvas', currentSym || 'BTCUSDT');
                    }, 50);
                }
            }
            
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }"""

new_switch_tab = """        function switchTab(tabId) {
            document.querySelectorAll('.tab-panel').forEach(p => {
                p.classList.remove('active');
                p.style.display = 'none';
            });
            document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));

            const targetPanel = document.getElementById(`tab-${tabId}`);
            if (targetPanel) {
                targetPanel.classList.add('active');
                targetPanel.style.display = 'block';
            }

            const navIndex = ['home', 'markets', 'trade', 'compounding', 'positions'].indexOf(tabId);
            if (navIndex !== -1) {
                const allNavs = document.querySelectorAll('.nav-item');
                if (allNavs[navIndex]) allNavs[navIndex].classList.add('active');
            }
            
            if (tabId === 'trade') {
                const currentSym = document.getElementById('tradeSymbol') ? document.getElementById('tradeSymbol').innerText : 'BTCUSDT';
                setTimeout(() => {
                    if (window.HermesMobileChart) {
                        HermesMobileChart.init('mobileChartCanvas', currentSym || 'BTCUSDT');
                    }
                }, 60);
            }
            
            window.scrollTo({ top: 0, behavior: 'instant' });
        }"""

if old_switch_tab in text:
    text = text.replace(old_switch_tab, new_switch_tab)
    print("Replaced switchTab with instant display logic.")
else:
    print("Could not find exact old_switch_tab, let's search loosely.")

# 3. Update bottom nav to explicitly show Chart with candlestick icon
old_bottom_nav_trade = """        <button class="nav-item" onclick="switchTab('trade')">
            <i class="fa-solid fa-chart-line"></i>
            <span>Futures</span>
        </button>"""

new_bottom_nav_trade = """        <button class="nav-item" onclick="switchTab('trade')">
            <i class="fa-solid fa-chart-candlestick"></i>
            <span>Chart</span>
        </button>"""

if old_bottom_nav_trade in text:
    text = text.replace(old_bottom_nav_trade, new_bottom_nav_trade)
    print("Replaced bottom nav Futures with Chart!")
else:
    print("Could not find old_bottom_nav_trade.")

with open(r'C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\static\mobile.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Saved updated static/mobile.html!")
