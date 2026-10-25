with open("static/mobile.html.bak_bitget_pro", "r", encoding="utf-8") as f:
    orig = f.read()

idx1 = orig.find('.bitget-pos-card {')
idx2 = orig.find('.nav-item {')
print("In backup, distance between .bitget-pos-card and .nav-item:", idx2 - idx1)
print("Snippet from backup between them:")
print(orig[idx2-500:idx2+100])
