import json

log_path = r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\.system_generated\logs\transcript.jsonl"
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            tc_list = data.get("tool_calls", [])
            for tc in tc_list:
                if "clean" in str(tc).lower() or "task-35360" in str(tc) or "81312" in str(tc):
                    print("Found TC:", tc)
        except Exception as e:
            pass
