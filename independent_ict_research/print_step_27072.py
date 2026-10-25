import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open(r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\.system_generated\logs\transcript.jsonl", "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        if idx == 27072:
            d = json.loads(line)
            print(d.get("content", ""))
            break
