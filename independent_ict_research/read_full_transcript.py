import json

with open(r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\.system_generated\logs\transcript_full.jsonl", "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        if idx == 27072:
            d = json.loads(line)
            c = d.get("content", "")
            with open("lecture4_untuncated.txt", "w", encoding="utf-8") as out:
                out.write(c)
            print("Wrote lecture4_untuncated.txt, length:", len(c))
            break
