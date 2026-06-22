import json

file_path = "results/Qwen3.6-35B-A3B-GGUF_results.jsonl"

with open(file_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= 20: break
        try:
            record = json.loads(line)
            print(f"[{record.get('id')}]: {repr(record.get('generated_sql'))} (type: {type(record.get('generated_sql'))})")
        except Exception as e:
            print(e)
