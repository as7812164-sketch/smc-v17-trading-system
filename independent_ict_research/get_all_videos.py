import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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
                    if any(w in c for w in ["Lecture", "Video", "Breakdown", "title", "Guardeer", "Smart Risk"]):
                        results[vid].append(c)
                except:
                    pass

with open("all_8_videos_summary.txt", "w", encoding="utf-8") as out:
    for vid, hits in results.items():
        out.write(f"\n=================== VIDEO {vid} ===================\n")
        for h in hits:
            # take first 400 chars
            snippet = h.strip()[:400].replace("\n", " ")
            out.write(f"- {snippet}\n")

print("Generated all_8_videos_summary.txt successfully!")
