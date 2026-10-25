import json
import re

with open(r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\.system_generated\logs\transcript_full.jsonl", "r", encoding="utf-8") as f:
    text = f.read()

video_ids = [
    'f18gazn0nYE', 'qEMhYlT6gwk', '4_33Wsc9fcg', 'zCj2SWbpmOk',
    '0zmD8iYhvpc', '46wLDbl2_d0', 'E8V1GHv5k5A', 'M5ccjwutWEY'
]

for vid in video_ids:
    print(f"\n=================== VIDEO ID: {vid} ===================")
    matches = re.findall(rf'.{{0,100}}{vid}.{{0,200}}', text)
    for m in matches[:4]:
        # print clean line
        clean = " ".join(m.split())
        print("  *", clean[:150])
