import json

video_ids = [
    'f18gazn0nYE', 'qEMhYlT6gwk', '4_33Wsc9fcg', 'zCj2SWbpmOk',
    '0zmD8iYhvpc', '46wLDbl2_d0', 'E8V1GHv5k5A', 'M5ccjwutWEY'
]

results = {vid: [] for vid in video_ids}

with open(r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\.system_generated\logs\transcript.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        for vid in video_ids:
            if vid in line:
                try:
                    d = json.loads(line)
                    c = d.get("content", "")
                    if "title" in c or "Video" in c or "Lecture" in c or "Breakdown" in c:
                        results[vid].append(c[:200])
                except:
                    pass

for vid, hits in results.items():
    print(f"\n=== VIDEO {vid} ===")
    for h in hits[:2]:
        print("  -", h.replace("\n", " ")[:150])
