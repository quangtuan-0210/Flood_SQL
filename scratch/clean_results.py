import json
import os

file_path = "results/Qwen3.6-35B-A3B-GGUF_results.jsonl"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

clean_records = []
removed_count = 0

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            record = json.loads(line)
            # Kiểm tra nếu generated_sql là None hoặc rỗng thì loại bỏ
            if record.get("generated_sql") is None or str(record.get("generated_sql")).strip() == "":
                removed_count += 1
            else:
                clean_records.append(record)
        except Exception as e:
            print(f"Error parsing line: {e}")

# Ghi đè lại file kết quả với các dòng sạch
with open(file_path, "w", encoding="utf-8") as f:
    for rec in clean_records:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"Đã loại bỏ {removed_count} câu bị rỗng (giấy trắng) từ file kết quả.")
print(f"Số câu còn lại giữ nguyên trong file: {len(clean_records)}")
