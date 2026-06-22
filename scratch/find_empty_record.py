import json

file_path = "results/Qwen3.6-35B-A3B-GGUF_results.jsonl"

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            record = json.loads(line)
            if record.get("id") == "L4_0003":
                print(f"Record L4_0003:")
                print(json.dumps(record, indent=2, ensure_ascii=False))
                break
        except Exception as e:
            print(e)
