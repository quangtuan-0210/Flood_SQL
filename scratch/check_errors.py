import json
import sqlglot
from sqlglot import parse_one

input_file = "results/Qwen3.6-35B-A3B-GGUF_results.jsonl"

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        try:
            record = json.loads(line)
        except Exception:
            continue
            
        qid = record.get("id")
        pred_sql = record.get("generated_sql")
        
        if not pred_sql:
            print(f"[{qid}]: Empty SQL (Null)")
            continue
            
        try:
            parse_one(pred_sql, read="duckdb")
        except Exception as e:
            print(f"[{qid}]: Parsing failed!")
            print(f"  Generated SQL: {repr(pred_sql)}")
            print(f"  Error: {e}\n")
