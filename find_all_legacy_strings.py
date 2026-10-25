import os

target_words = ['HERMES 3.0', 'Hermes 3.0', 'Hermes 2.0', 'HERMES 2.0', 'HERMES 2.5', 'Hermes 2.5', 'SMC V17', 'SMC v17', 'smc_v17']
ignore_dirs = ['.git', '__pycache__', 'historical_data', 'market_data_cache', '.gemini']

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ignore_dirs]
    for f in files:
        if f.endswith(('.py', '.html', '.json', '.env')):
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                    for i, line in enumerate(fp, 1):
                        for tw in target_words:
                            if tw in line:
                                print(f"{p}:{i} [{tw}] -> {line.encode('ascii', 'replace').decode('ascii').strip()[:90]}")
            except Exception:
                pass
