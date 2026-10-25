with open("static/mobile.html", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('<nav class="bottom-nav">')
end = text.find('</nav>', idx)
print(text[idx:end+6])
