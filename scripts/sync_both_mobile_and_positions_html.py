import re

# 1. Update static/mobile.html
with open("static/mobile.html", "r", encoding="utf-8") as f:
    m_html = f.read()

# Update mapping in mobile.html
idx_map_start = m_html.find("container.innerHTML = data.positions.map(p => {")
if idx_map_start != -1:
    m_html = m_html[:idx_map_start] + "const cardsHtml = data.positions.map(p => {" + m_html[idx_map_start + len("container.innerHTML = data.positions.map(p => {"):]
    print("Replaced container.innerHTML with const cardsHtml!")

idx_map_end = m_html.find("}).join('');\n                }", idx_map_start)
if idx_map_end != -1:
    inject_both = """}).join('');
                    container.innerHTML = cardsHtml;
                    const homeContainer = document.getElementById('homePositionsContainer');
                    const homeSection = document.getElementById('homePositionsSection');
                    const homePosCount = document.getElementById('homePosCount');
                    if (homeContainer && homeSection) {
                        homeContainer.innerHTML = cardsHtml;
                        homeSection.style.display = data.positions.length > 0 ? 'block' : 'none';
                        if (homePosCount) homePosCount.textContent = data.positions.length;
                    }
                }"""
    m_html = m_html[:idx_map_end] + inject_both + m_html[idx_map_end + len("}).join('');\n                }"):]
    print("Injected dual-rendering to home and positions tabs!")

# Also handle empty state on home tab
idx_empty = m_html.find("container.innerHTML = `\n                        <div class=\"empty-radar\">")
if idx_empty != -1:
    m_html = m_html[:idx_empty] + "const homeSec = document.getElementById('homePositionsSection'); if (homeSec) homeSec.style.display = 'none';\n                    " + m_html[idx_empty:]
    print("Added empty state handling for home tab!")

with open("static/mobile.html", "w", encoding="utf-8") as f:
    f.write(m_html)
print("Updated static/mobile.html successfully!")

# -------------------------------------------------------------------
# 2. Update static/positions.html to match Bitget Pro layout
# -------------------------------------------------------------------
with open("static/positions.html", "r", encoding="utf-8") as f:
    p_html = f.read()

# Replace bitget-pos-card CSS in positions.html
pos_css_start = p_html.find(".bitget-pos-card {")
if pos_css_start != -1:
    pos_css_end = p_html.find("/* =========================================================\n           DESKTOP TOPBAR & CONTROLS", pos_css_start)
    if pos_css_end == -1:
        pos_css_end = p_html.find(".bitget-dock-btn", pos_css_start)
    print("Found positions.html CSS around:", pos_css_start, "to", pos_css_end)

# Let's inspect where render positions is in positions.html
idx_p_render = p_html.find("<div class=\"bitget-pos-card\" id=\"card-${pos.id}\">")
if idx_p_render != -1:
    idx_p_end = p_html.find("</div>\n                    `;", idx_p_render)
    print("Found positions.html card template from", idx_p_render, "to", idx_p_end)

