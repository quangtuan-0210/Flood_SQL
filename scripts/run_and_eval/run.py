import os
import json
import numpy as np
import time 
import argparse
import glob
import duckdb
from openai import OpenAI

INPUT_JSON = "benchmark/bechmark_updated.jsonl" 

OUTPUT_JSONL = "results/Qwen3.6-35B-A3B-GGUF_results.jsonl"

DATA_DIR = "data"
METADATA_PATH = os.path.join(DATA_DIR, "metadata_parquet.json")
CACHE_FILE = "embedding_cache_mirai.json"

# Khai báo model LLM sinh SQL và Embedding
MODEL_NAME = "vllm/Qwen3.6-35B-A3B-GGUF"
LLM_API_BASE = "https://appresearchpublic83.aiplatform.vcntt.tech/v1"
LLM_API_KEY = "sglang"

EMBEDDING_MODEL = "mirai-embedding"
EMBEDDING_API_BASE = "https://embedding.openclassroomteam.com/v1"
EMBEDDING_API_KEY = "f0GVKMTEP4VBkjjAymxyYftvi6xX2mVz"

client_llm = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_API_BASE
)

client_emb = OpenAI(
    api_key=EMBEDDING_API_KEY,
    base_url=EMBEDDING_API_BASE
)

# =========================================================
# HELPERS (API EMBEDDING & CACHE)
# =========================================================
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        EMBEDDING_CACHE = json.load(f)
else:
    EMBEDDING_CACHE = {}

def embed(text: str):
    if text in EMBEDDING_CACHE:
        return np.array(EMBEDDING_CACHE[text])
    
    # Gọi API Embedding qua OpenAI client
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = client_emb.embeddings.create(
                model=EMBEDDING_MODEL,
                input=[text],
                timeout=30
            )
            vec = resp.data[0].embedding
            break
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"[ERROR] Không thể lấy embedding cho '{text[:30]}...': {e}")
                raise e
            time.sleep(2 ** attempt)
            
    EMBEDDING_CACHE[text] = vec
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(EMBEDDING_CACHE, f)
    return np.array(vec)

def cosine(a, b):
    denom = (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10)
    return float(np.dot(a, b) / denom)

def clean_sql(sql: str):
    return sql.strip().replace("```sql", "").replace("```", "").strip()

def flatten_sql(sql: str) -> str:
    return " ".join(sql.split())

def load_metadata(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# =========================================================
# BUILD TABLE + COLUMN DESCRIPTION CORPUS
# =========================================================
def build_table_index(meta):
    table_texts = {}
    for table, info in meta.items():
        if table == "_global": continue
        desc_parts = [table]
        for col in info.get("schema", []):
            cname = col.get("column_name", "")
            cdesc = col.get("description", "")
            desc_parts.append(f"{cname}: {cdesc}")
        table_texts[table] = "\n".join(desc_parts)
    return table_texts

def build_column_index(meta):
    col_index = {}
    for table, info in meta.items():
        if table == "_global": continue
        items = []
        for col in info.get("schema", []):
            cname = col.get("column_name", "")
            cdesc = col.get("description", "")
            text = f"{cname}: {cdesc}"
            items.append((cname, text))
        col_index[table] = items
    return col_index

def retrieve_tables(question, table_index, top_k):
    q_emb = embed(question)
    scores = []
    for table, text in table_index.items():
        t_emb = embed(text)
        scores.append((table, cosine(q_emb, t_emb)))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    top_tables = [t for t, s in scores[:top_k]]
    return top_tables, scores[:top_k]

def retrieve_columns(question, col_index, chosen_tables):
    q_emb = embed(question)
    result = {}
    critical_cols = {"geoid", "countyfp", "statefp", "countyfips", "geometry", "lon", "lat"}
    for table in chosen_tables:
        cols = col_index[table]
        col_scores = []
        for cname, ctext in cols:
            cemb = embed(ctext)
            score = cosine(q_emb, cemb)
            col_scores.append((cname, score, ctext))
        col_scores = sorted(col_scores, key=lambda x: x[1], reverse=True)
        
        # Lấy top 10 cột hàng đầu (tăng từ 5 lên 10 để bao phủ tốt hơn)
        top_k_cols = col_scores[:10] if len(col_scores) >= 10 else col_scores
        top_names = {c[0].lower() for c in top_k_cols}
        
        # Bắt buộc đưa các cột khóa nối (join keys) và cột hình học (spatial) vào context nếu chưa được chọn
        for cname, score, ctext in col_scores:
            if cname.lower() in critical_cols and cname.lower() not in top_names:
                top_k_cols.append((cname, score, ctext))
                
        result[table] = top_k_cols
    return result

def build_metadata_prompt(meta, chosen_tables, chosen_columns):
    lines = []
    lines.append("[TABLES SELECTED]")
    for t in chosen_tables: lines.append(f"- {t}")
    lines.append("\n[COLUMNS SELECTED]")
    for t, cols in chosen_columns.items():
        for cname, score, cdesc in cols: lines.append(f"- {t}.{cname}: {cdesc}")
    jr = meta["_global"].get("join_rules", {})
    for k1 in ["direct", "concat"]:
        for it in jr.get("key_based", {}).get(k1, []):
            p = it.get("pair", [])
            if len(p) == 2: lines.append(f"- {p[0]}  <->  {p[1]}")
    for k2 in ["point_polygon", "polygon_polygon"]:
        for it in jr.get("spatial", {}).get(k2, []):
            p = it.get("pair", [])
            if len(p) == 2: lines.append(f"- {p[0]}  <->  {p[1]}")
    lines.append("\n[RULES]")
    for k, v in meta["_global"].get("rules", {}).items(): lines.append(f"- {k}: {v}")
    
    result = "\n".join(lines)
    if len(result) > 80000:
        result = result[:80000] + "\n...[TRUNCATED]..."
    return result

# =========================================================
# MAIN PIPELINE (CÓ TÍNH NĂNG CHẠY TIẾP SỨC - RESUME)
# =========================================================
SYSTEM_PROMPT = """You are an expert DuckDB SQL generator for the FloodSQL_Bench dataset.
Use only the tables and columns given in the metadata context.
Do NOT output any reasoning, explanation, or analysis.
Output only the final SQL query, with no comments and no semicolon.
Your output must contain SQL code only.

CRITICAL RULES FOR PERFORMANCE & SPATIAL JOINS:
1. When performing a spatial join/filter (like ST_Intersects, ST_Contains, or ST_Within) between another table and the 'floodplain' table, if the query filters by state (e.g., STATEFP = '12' or GEOID starting with a state prefix), you MUST explicitly apply the same state filter to the 'floodplain' table as well (e.g., floodplain.STATEFP = '12' or floodplain.GEOID LIKE '12%'). Failing to do so causes a massive cross-join on the entire 2.5 GB floodplain dataset, leading to a query timeout!
2. Apply state/county filters on all joined tables as early as possible to minimize geometric calculation overhead."""

def generate_sql_rag_embed():
    meta = load_metadata(METADATA_PATH)
    table_index = build_table_index(meta)
    col_index = build_column_index(meta)

    # Khởi tạo kết quả DuckDB để kiểm tra lỗi cú pháp và đặt tên cột trước khi lưu
    print("Đang khởi động DuckDB cục bộ phục vụ bước Self-Correction...")
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL spatial;")
    con.execute("LOAD spatial;")
    for filepath in glob.glob(os.path.join(DATA_DIR, "*.parquet")):
        filename = os.path.basename(filepath)
        table_name = filename.replace('.parquet', '').replace('_tx_fl_la', '')
        try:
            con.execute(f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM '{filepath}'")
        except Exception:
            pass

    # Đảm bảo thư mục results tồn tại
    os.makedirs(os.path.dirname(OUTPUT_JSONL), exist_ok=True)
    
    # BƯỚC 1: ĐỌC NHỮNG CÂU ĐÃ LÀM TỪ Ổ CỨNG
    processed_ids = set()
    if os.path.exists(OUTPUT_JSONL):
        with open(OUTPUT_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    processed_ids.add(record["id"])
                except Exception:
                    pass
    
    if len(processed_ids) > 0:
        print(f"⏩ Đã tìm thấy {len(processed_ids)} câu hoàn thành trong '{OUTPUT_JSONL}'. Chạy tiếp...")

    # BƯỚC 2: MỞ FILE CHẾ ĐỘ APPEND ("a")
    fout = open(OUTPUT_JSONL, "a", encoding="utf-8")

    qa_data = []
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        for line in f:
            qa_data.append(json.loads(line))

    for item in qa_data:
        qid = item["id"]
        
        # BƯỚC 3: KIỂM TRA TRÙNG LẶP
        if qid in processed_ids:
            continue

        question = item["question"]
        level = item["id"][:2]
        print(f"\n[{qid}] Đang xử lý:\n{question}")

        top_k = 3 if level.startswith("L0") else (4 if level.startswith("L1") or level.startswith("L2") else 5)
        chosen_tables, table_scores = retrieve_tables(question, table_index, top_k)
        chosen_columns = retrieve_columns(question, col_index, chosen_tables)
        metadata_prompt = build_metadata_prompt(meta, chosen_tables, chosen_columns)

        user_prompt = f"Question:\n{question}\n\nReturn only a single valid DuckDB SQL query."

        sql = None
        max_attempts = 3
        
        # Danh sách hội thoại gửi LLM (sẽ append thêm nếu có lỗi cú pháp để tự sửa)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": metadata_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        for attempt in range(max_attempts):
            raw_sql = None
            api_success = False
            # Lần thử gọi API (có retry 5 lần đối với lỗi kết nối)
            for api_retry in range(5):
                try:
                    resp = client_llm.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages,
                        temperature=0,
                        timeout=120
                    )
                    raw_sql = clean_sql(resp.choices[0].message.content)
                    raw_sql = flatten_sql(raw_sql)
                    api_success = True
                    break
                except Exception as e:
                    print(f"[CẢNH BÁO] API call thất bại lần {api_retry + 1} tại {qid}: {e}")
                    time.sleep(2 ** api_retry)
            
            if not api_success or not raw_sql:
                print(f"[ERROR] API thất bại hoàn toàn tại {qid}")
                break
                
            # Kiểm tra cú pháp bằng EXPLAIN
            try:
                con.execute(f"EXPLAIN {raw_sql}")
                sql = raw_sql
                if attempt > 0:
                    print(f"  -> [SỬA LỖI THÀNH CÔNG] Đã tự sửa lỗi thành công ở lần thử {attempt + 1}")
                break
            except Exception as duckdb_err:
                err_msg = str(duckdb_err).strip()
                print(f"  -> [LỖI CÚ PHÁP/CỘT] Lần thử {attempt + 1} tại {qid} lỗi: {err_msg}")
                # Đưa câu sai và lỗi của DuckDB vào lịch sử để LLM sửa
                messages.append({"role": "assistant", "content": raw_sql})
                correction_prompt = (
                    f"The SQL query you generated failed execution in DuckDB with the following error:\n"
                    f"{err_msg}\n\n"
                    f"Please correct the error, ensure all column names and table names match the schema metadata, and return only the corrected SQL query with no explanation."
                )
                messages.append({"role": "user", "content": correction_prompt})

        record = {
            "id": qid,
            "question": question,
            "gt_sql": item.get("sql", None),
            "generated_sql": sql,
            "chosen_tables": chosen_tables,
            "chosen_columns": {t: [c for c, _, d in cols] for t, cols in chosen_columns.items()},
            "table_scores": table_scores,
        }
        
        # Ghi và Lưu thẳng xuống ổ cứng sau mỗi câu
        fout.write(json.dumps(record, ensure_ascii=False) + "\n")
        fout.flush() 

    fout.close()
    print(f"\n[HOÀN THÀNH] Đã xử lý toàn bộ và lưu tại {OUTPUT_JSONL}")

if __name__ == "__main__":
    generate_sql_rag_embed()