import glob

files = glob.glob("static/*.html")
for path in files:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    has_pro = "/pro-charts" in content or "pro_charts.html" in content
    has_markets = "/markets" in content
    has_hermes = "/hermes-ai" in content
    print(f"{path}: pro-charts={has_pro}, markets={has_markets}, hermes-ai={has_hermes}")
