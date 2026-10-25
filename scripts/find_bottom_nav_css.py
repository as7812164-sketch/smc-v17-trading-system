with open("static/mobile.html.bak_bitget_pro", "r", encoding="utf-8") as f:
    orig = f.read()

idx = orig.find('.bottom-nav')
print("In backup, .bottom-nav found at:", idx)
if idx != -1:
    print(orig[idx-100:idx+800])
