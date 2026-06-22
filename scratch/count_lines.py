import json

file_path = "results/Qwen3.6-35B-A3B-GGUF_results.jsonl"

total = 0
null_count = 0

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        total += 1
        try:
            record = json.loads(line)
            if record.get("generated_sql") is None:
                null_count += 1
        except Exception as e:
            pass

print(f"Total lines: {total}")
print(f"Null generated_sql: {null_count}")
