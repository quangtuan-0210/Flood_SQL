import os
import json
import glob
import sys
import duckdb
import pandas as pd
import numpy as np
import sqlglot
import threading
from sqlglot import exp, parse_one

# Đảm bảo đường dẫn import hoạt động
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from weighted_ast_similarity import compare_queries, decompose_query, resolve_aliases, normalize_predicates
from tree_edit_distance import calculate_tree_edit_distance_similarity

INPUT_FILE = "results/Qwen3.6-35B-A3B-GGUF_results.jsonl"
OUTPUT_REPORT_WEIGHTED = "results/experiment_results_weighted_ast.md"
OUTPUT_REPORT_TED = "results/experiment_results_tree_edit_distance.md"
DATA_DIR = "data"

class TimeoutConnection:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.con = self._init_db()

    def _init_db(self):
        con = duckdb.connect(database=':memory:')
        con.execute("INSTALL spatial;")
        con.execute("LOAD spatial;")
        for filepath in glob.glob(os.path.join(self.data_dir, "*.parquet")):
            filename = os.path.basename(filepath)
            table_name = filename.replace('.parquet', '').replace('_tx_fl_la', '')
            con.execute(f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM '{filepath}'")
        return con

    def execute(self, sql, timeout_sec=3.0):
        interrupted = False
        query_finished = False
        lock = threading.Lock()
        
        def interrupt_func():
            nonlocal interrupted
            with lock:
                if query_finished:
                    return
                interrupted = True
                try:
                    self.con.interrupt()
                except Exception:
                    pass

        timer = threading.Timer(timeout_sec, interrupt_func)
        try:
            timer.start()
            df = self.con.execute(sql).fetchdf()
            with lock:
                query_finished = True
                if interrupted:
                    raise duckdb.InterruptException("Query timed out")
            return df
        except duckdb.InterruptException:
            with lock:
                query_finished = True
            try:
                self.con.close()
            except Exception:
                pass
            self.con = self._init_db()
            raise
        finally:
            with lock:
                query_finished = True
            timer.cancel()

def compare_results(df1, df2):
    if df1 is None or df2 is None:
        return False
    if df1.shape != df2.shape:
        return False
    df2.columns = df1.columns
    df1 = df1.sort_values(by=df1.columns.tolist()).reset_index(drop=True)
    df2 = df2.sort_values(by=df2.columns.tolist()).reset_index(drop=True)
    try:
        pd.testing.assert_frame_equal(df1, df2, check_dtype=False, check_exact=False, atol=1e-3)
        return True
    except AssertionError:
        return False

def check_exec_accuracy(db, gt_sql, gen_sql):
    if not gen_sql:
        return False
    try:
        df_gt = db.execute(gt_sql, timeout_sec=5.0)
    except Exception:
        df_gt = None
        
    try:
        df_gen = db.execute(gen_sql, timeout_sec=3.0)
    except Exception:
        df_gen = None
        
    if df_gt is not None and df_gen is not None:
        return compare_results(df_gt, df_gen)
    return False

def calculate_text_similarity(sql1, sql2):
    if not sql1 or not sql2:
        return 0.0
    tokens1 = set(sql1.lower().split())
    tokens2 = set(sql2.lower().split())
    if not tokens1 and not tokens2:
        return 1.0
    if not tokens1 or not tokens2:
        return 0.0
    return len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2))

def format_ast_tree(node, indent=0):
    if node is None:
        return ""
    lines = []
    node_name = node.__class__.__name__
    lines.append("  " * indent + f"└─ {node_name}")
    # Inspect arguments
    for k, v in node.args.items():
        if v is None:
            continue
        if isinstance(v, list):
            for item in v:
                if isinstance(item, exp.Expression):
                    lines.append(format_ast_tree(item, indent + 1))
        elif isinstance(v, exp.Expression):
            lines.append(format_ast_tree(v, indent + 1))
    return "\n".join(lines)

def get_ast_viz(sql_str):
    try:
        ast = parse_one(sql_str, read="duckdb")
        normalized = resolve_aliases(ast)
        normalized = normalize_predicates(normalized)
        return format_ast_tree(normalized)
    except Exception:
        return "└─ Syntax Error (Lỗi cú pháp)"

def generate_report():
    print("Đang khởi động DuckDB và tải dữ liệu...")
    db = TimeoutConnection(DATA_DIR)
    
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Không tìm thấy file kết quả tại '{INPUT_FILE}'! Vui lòng chạy file run.py trước.")
        return
        
    print(f"Đọc dữ liệu kết quả từ '{INPUT_FILE}'...")
    records = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                pass
                
    if not records:
        print("[ERROR] File kết quả rỗng!")
        return

    # Duyệt qua từng phương pháp so sánh tương đồng để tạo báo cáo riêng biệt
    for mode in ["weighted_ast", "tree_edit_distance"]:
        if mode == "weighted_ast":
            output_report = OUTPUT_REPORT_WEIGHTED
            report_title = "BÁO CÁO THỰC NGHIỆM ĐÁNH GIÁ TRUY VẤN TEXT-TO-SPATIAL SQL (WEIGHTED AST)"
            metric_col_header = "Điểm tương đồng Weighted AST (Weighted AST Similarity)"
            print("Đang xử lý báo cáo cho phương pháp Weighted AST...")
        else:
            output_report = OUTPUT_REPORT_TED
            report_title = "BÁO CÁO THỰC NGHIỆM ĐÁNH GIÁ TRUY VẤN TEXT-TO-SPATIAL SQL (TREE EDIT DISTANCE)"
            metric_col_header = "Điểm tương đồng Tree Edit Distance (TED Similarity)"
            print("Đang xử lý báo cáo cho phương pháp Tree Edit Distance (TED)...")

        # 1. Tính toán điểm số theo từng mức L0-L6
        levels = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
        level_stats = {l: {"exec": [], "metric": [], "text": []} for l in levels}
        
        evaluated_records = []
        for rec in records:
            qid = rec["id"]
            level = qid[:2]
            if level not in level_stats:
                continue
                
            gt_sql = rec.get("gt_sql") or rec.get("sql")
            gen_sql = rec.get("generated_sql")
            
            # Điểm thực thi
            exec_ok = check_exec_accuracy(db, gt_sql, gen_sql)
            exec_score = 1.0 if exec_ok else 0.0
            
            # Điểm tương đồng tương ứng
            if mode == "weighted_ast":
                ast_res = compare_queries(gt_sql, gen_sql)
                metric_score = 0.0 if "error" in ast_res else ast_res["score"]
                res_details = ast_res
            else:
                ted_res = calculate_tree_edit_distance_similarity(gt_sql, gen_sql)
                metric_score = ted_res["score"]
                res_details = ted_res
                
            # Điểm tương đồng văn bản
            text_score = calculate_text_similarity(gt_sql, gen_sql)
            
            # Lưu kết quả
            level_stats[level]["exec"].append(exec_score)
            level_stats[level]["metric"].append(metric_score)
            level_stats[level]["text"].append(text_score)
            
            evaluated_records.append({
                "id": qid,
                "level": level,
                "question": rec["question"],
                "gt_sql": gt_sql,
                "gen_sql": gen_sql,
                "exec_ok": exec_ok,
                "metric_score": metric_score,
                "text_score": text_score,
                "details": res_details
            })
            
        # Lập bảng so sánh cấp độ L0-L6
        comparison_table_lines = [
            f"| Mức độ | Số lượng câu | Độ chính xác thực thi (Execution Acc) | {metric_col_header} | Điểm tương đồng văn bản SQL (Text Similarity) |",
            "| :--- | :---: | :---: | :---: | :---: |"
        ]
        
        total_exec, total_metric, total_text = [], [], []
        total_count = 0
        
        for l in levels:
            stats = level_stats[l]
            count = len(stats["exec"])
            if count == 0:
                continue
            avg_exec = np.mean(stats["exec"])
            avg_metric = np.mean(stats["metric"])
            avg_text = np.mean(stats["text"])
            
            total_exec.extend(stats["exec"])
            total_metric.extend(stats["metric"])
            total_text.extend(stats["text"])
            total_count += count
            
            comparison_table_lines.append(
                f"| {l} | {count} | {avg_exec * 100:.2f}% | {avg_metric * 100:.2f}% | {avg_text * 100:.2f}% |"
            )
            
        # Dòng Trung bình cộng
        comparison_table_lines.append(
            f"| **Trung bình cộng** | **{total_count}** | **{np.mean(total_exec)*100:.2f}%** | **{np.mean(total_metric)*100:.2f}%** | **{np.mean(total_text)*100:.2f}%** |"
        )
        
        # 2. Lựa chọn tối thiểu 12 cặp SQL (L0-L5) đại diện
        candidate_records = [r for r in evaluated_records if r["level"] in ["L0", "L1", "L2", "L3", "L4", "L5"]]
        
        selected_records = []
        for l in ["L0", "L1", "L2", "L3", "L4", "L5"]:
            level_recs = [r for r in candidate_records if r["level"] == l]
            correct_recs = [r for r in level_recs if r["exec_ok"]]
            incorrect_recs = [r for r in level_recs if not r["exec_ok"]]
            
            if correct_recs:
                selected_records.append(correct_recs[0])
            if incorrect_recs:
                selected_records.append(incorrect_recs[0])
                
        if len(selected_records) < 12:
            used_ids = {r["id"] for r in selected_records}
            remaining = [r for r in candidate_records if r["id"] not in used_ids]
            selected_records.extend(remaining[:(12 - len(selected_records))])
            
        selected_records = selected_records[:12]
        
        # Lập bảng so sánh 12 cặp
        pairs_table_lines = [
            f"| Cặp số | Mã câu hỏi | Mức độ | Điểm tương đồng {('Weighted AST' if mode == 'weighted_ast' else 'TED')} | Kết quả Thực thi | Nhận xét chi tiết nguyên nhân khác biệt |",
            "| :---: | :--- | :---: | :---: | :---: | :--- |"
        ]
        
        pair_details_sections = []
        for idx, r in enumerate(selected_records):
            pair_num = idx + 1
            qid = r["id"]
            lvl = r["level"]
            m_score = r["metric_score"]
            exec_ok = "Đúng" if r["exec_ok"] else "Sai"
            
            # Tạo nhận xét
            comment = ""
            details = r["details"]
            
            if mode == "weighted_ast":
                expl = details.get("explanations", {})
                if "error" in details:
                    comment = "Lỗi cú pháp: Mô hình sinh ra câu lệnh lỗi hoặc rỗng."
                elif r["exec_ok"]:
                    if m_score == 1.0:
                        comment = "Khớp hoàn toàn: Cả cú pháp và cấu trúc ngữ nghĩa khớp 100%."
                    else:
                        comment = "Khác biệt cú pháp: Khác alias hoặc thứ tự bảng/mệnh đề điều kiện nhưng tương đương ngữ nghĩa."
                else:
                    if expl.get("tables", {}).get("missing"):
                        comment = f"Sai bảng: Chọn thiếu bảng cần truy vấn ({', '.join(expl['tables']['missing'])})."
                    elif expl.get("join_conditions", {}).get("missing"):
                        comment = "Thiếu kết nối: Câu lệnh thiếu điều kiện JOIN không gian hoặc khóa ngoại."
                    elif expl.get("filter_conditions", {}).get("missing"):
                        comment = "Thiếu bộ lọc: Thiếu các điều kiện lọc WHERE cần thiết."
                    else:
                        comment = "Sai logic: Khác biệt ở cấu trúc SELECT hoặc cách lập điều kiện."
            else:  # tree_edit_distance
                dist = details.get("distance", 0)
                size1 = details.get("size1", 0)
                size2 = details.get("size2", 0)
                if size1 == 0 and size2 == 0:
                    comment = "Cả hai truy vấn đều rỗng hoặc lỗi cú pháp nặng."
                elif size2 == 0:
                    comment = "Lỗi cú pháp: Predicted SQL rỗng hoặc không thể parse thành cây AST."
                elif r["exec_ok"]:
                    if dist == 0:
                        comment = "Khớp hoàn toàn: Cấu trúc AST của hai truy vấn trùng khớp 100%."
                    else:
                        comment = f"Tương đương kết quả: Khác biệt cấu trúc nhẹ (Khoảng cách = {dist}), kết quả chạy khớp."
                else:
                    comment = f"Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = {dist} trên tổng {size1 + size2} nút)."

            pairs_table_lines.append(
                f"| {pair_num} | {qid} | {lvl} | {m_score:.2f} | {exec_ok} | {comment} |"
            )
            
            # Tạo trực quan hóa cây AST
            gt_ast_viz = get_ast_viz(r["gt_sql"])
            gen_ast_viz = get_ast_viz(r["gen_sql"])
            
            if mode == "weighted_ast":
                expl = details.get("explanations", {})
                detail_analysis = f"""- **Nhận xét**: {comment}
- **Thành phần khớp**: {json.dumps(expl.get("tables", {}).get("matches", []) if "error" not in details else [], ensure_ascii=False)}
- **Thành phần thiếu (Ground Truth có nhưng Predicted thiếu)**: {json.dumps(expl.get("filter_conditions", {}).get("missing", []) + expl.get("join_conditions", {}).get("missing", []) if "error" not in details else [], ensure_ascii=False)}
- **Thành phần thừa (Predicted tự viết thêm)**: {json.dumps(expl.get("filter_conditions", {}).get("extra", []) + expl.get("join_conditions", {}).get("extra", []) if "error" not in details else [], ensure_ascii=False)}"""
            else:
                dist = details.get("distance", 0)
                size1 = details.get("size1", 0)
                size2 = details.get("size2", 0)
                detail_analysis = f"""- **Nhận xét**: {comment}
- **Khoảng cách hiệu chỉnh cây (Tree Edit Distance)**: {dist}
- **Kích thước cây Ground Truth (Ground Truth AST Size)**: {size1} nút
- **Kích thước cây Predicted (Predicted AST Size)**: {size2} nút
- **Tổng số nút tối đa (Max Possible Distance)**: {size1 + size2}"""

            pair_details_sections.append(f"""
### Cặp {pair_num}: {qid} (Mức {lvl})
* **Câu hỏi**: {r["question"]}
* **Điểm tương đồng {('Weighted AST' if mode == 'weighted_ast' else 'TED')}**: {m_score:.2f}
* **Độ chính xác thực thi**: {exec_ok}

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  {r["gt_sql"]}
  ```
* **Predicted SQL**:
  ```sql
  {r["gen_sql"] if r["gen_sql"] else "(Trống)"}
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
{gt_ast_viz}

CÂY AST PREDICTED:
{gen_ast_viz}
```

#### Phân tích lỗi và khác biệt:
{detail_analysis}

---
""")

        # 3. Kết hợp toàn bộ nội dung thành báo cáo hoàn chỉnh
        comparison_table_md = "\n".join(comparison_table_lines)
        pairs_table_md = "\n".join(pairs_table_lines)
        pair_details_md = "\n".join(pair_details_sections)
        
        if mode == "weighted_ast":
            desc_text = r"""- **Điểm tương đồng Weighted AST (Weighted AST Similarity)** đo lường độ chính xác cấu trúc ngữ nghĩa (phân tích sâu các thành phần SELECT, WHERE, JOIN, FROM, Predicate phi không gian, GROUP BY, ORDER BY theo hệ số trọng số), phản ánh sát tư duy viết code của AI."""
        else:
            desc_text = r"""- **Điểm tương đồng Tree Edit Distance (TED Similarity)** đo lường số bước sửa đổi tối thiểu trên cây cú pháp AST đã chuẩn hóa để biến đổi truy vấn Predicted thành Ground Truth.
  
  **Thuật toán Tree Edit Distance (TED):**
  Phương pháp sử dụng thuật toán Zhang-Shasha (1989) để so sánh hai cây cú pháp có thứ tự. Khoảng cách hiệu chỉnh $d(T_1, T_2)$ là số thao tác tối thiểu gồm:
  1. *Delete (Xóa nút)*: Loại bỏ một nút khỏi cây và chuyển các con của nó lên làm con trực tiếp của cha nó.
  2. *Insert (Thêm nút)*: Chèn thêm một nút vào một vị trí và chuyển một nhóm con của cha nó làm con của nút mới.
  3. *Rename (Thay đổi nhãn)*: Đổi nhãn của một nút (ví dụ: đổi tên hàm hoặc cột).
  
  **Công thức chuẩn hóa điểm tương đồng:**
  Điểm tương đồng chuẩn hóa $S \in [0, 1]$ được tính theo công thức:
  $$S = 1.0 - \frac{d(T_1, T_2)}{|T_1| + |T_2|}$$
  *Trong đó:*
  - $d(T_1, T_2)$ là khoảng cách hiệu chỉnh cây thực tế giữa Ground Truth AST ($T_1$) và Predicted AST ($T_2$).
  - $|T_1| + |T_2|$ là khoảng cách hiệu chỉnh tối đa có thể (trường hợp xóa sạch cây $T_1$ và dựng mới toàn bộ cây $T_2$).
  - Nếu cả hai cây đều rỗng ($|T_1| + |T_2| = 0$), $S = 1.0$."""

        report_content = f"""# {report_title}

Báo cáo này được tự động tạo lập từ kết quả chạy đánh giá mô hình `vllm/Qwen3.6-35B-A3B-GGUF` kết hợp với API embedding `mirai-embedding` trên tập dữ liệu FloodSQL-Bench.

## 1. Bảng So sánh Hiệu năng Theo Cấp độ (L0 - L6)

Dưới đây là bảng thống kê điểm số trung bình của mô hình theo từng mức từ L0 (Dễ nhất) đến L6 (Khó nhất):

{comparison_table_md}

* **Nhận xét chung**:
  - **Độ chính xác thực thi (Execution Accuracy)** phản ánh tỷ lệ câu chạy ra kết quả khớp 100% trên DuckDB.
  {desc_text}
  - **Điểm tương đồng văn bản (Text Similarity)** dựa trên từ vựng thuần túy, thường có xu hướng thấp hơn điểm AST do sự khác biệt nhỏ về cách viết thường/hoa, khoảng trắng hoặc alias không làm ảnh hưởng ngữ nghĩa nhưng làm lệch chữ.

## 2. Bảng So sánh 12 Cặp Spatial SQL Tiêu Biểu (L0 - L5)

Dưới đây là bảng thống kê 12 cặp truy vấn đại diện được trích xuất từ thực nghiệm để đánh giá chi tiết:

{pairs_table_md}

## 3. Phân tích Chi tiết 12 Cặp Truy vấn (AST & Trực quan hóa)

{pair_details_md}
"""

        os.makedirs(os.path.dirname(output_report), exist_ok=True)
        with open(output_report, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        print(f"[HOÀN THÀNH] Đã tạo báo cáo thực nghiệm chi tiết tại: {output_report}")

if __name__ == "__main__":
    generate_report()
