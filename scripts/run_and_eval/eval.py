import json
import duckdb
import pandas as pd
import warnings
import os
import glob
import sys
import threading

# Đảm bảo đường dẫn import tương đối hoạt động
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from semantic_similarity import compare_queries

warnings.filterwarnings('ignore')

INPUT_FILE = "results/Qwen3.6-35B-A3B-GGUF_results.jsonl" 
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
    """So sánh 2 bảng dữ liệu kết quả, bỏ qua tên cột và thứ tự dòng"""
    if df1 is None or df2 is None:
        return False
    if df1.shape != df2.shape:
        return False
    
    # Ép tên cột giống nhau để so sánh
    df2.columns = df1.columns
    
    # Sắp xếp lại thứ tự dòng để không bị chấm sai do vị trí lộn xộn
    df1 = df1.sort_values(by=df1.columns.tolist()).reset_index(drop=True)
    df2 = df2.sort_values(by=df2.columns.tolist()).reset_index(drop=True)
    
    try:
        # So sánh, cho phép sai số cực nhỏ với số thập phân (float)
        pd.testing.assert_frame_equal(df1, df2, check_dtype=False, check_exact=False, atol=1e-3)
        return True
    except AssertionError:
        return False

def main():
    print("Khởi tạo cơ sở dữ liệu DuckDB và nạp các bảng dữ liệu...")
    if not os.path.exists(DATA_DIR):
        print(f"Không tìm thấy thư mục '{DATA_DIR}'! Hãy chắc chắn bạn đang chạy lệnh từ thư mục gốc của project.")
        return
        
    db = TimeoutConnection(DATA_DIR)
    print("=" * 50)
    
    total = 0
    correct = 0
    syntax_errors = 0
    wrong_logic = 0
    
    # Danh sách lưu điểm tương đồng AST
    ast_scores = []
    
    # Thống kê loại lỗi AST
    missing_tables = 0
    missing_filters = 0
    missing_joins = 0
    
    print(f"\n📖 Bắt đầu chấm thi từ: {INPUT_FILE}\n")
    print("-" * 50)
    
    # Kiểm tra xem file kết quả có tồn tại không
    if not os.path.exists(INPUT_FILE):
        print(f"Không tìm thấy file kết quả tại '{INPUT_FILE}'. Vui lòng kiểm tra lại đường dẫn!")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            total += 1
            qid = item.get('id', f"Q_{total}")
            
            gt_sql = item.get('gt_sql', '').strip()
            gen_sql = item.get('generated_sql', '')
            
            # Tính toán tương đồng AST
            res_ast = compare_queries(gt_sql, gen_sql)
            if "error" in res_ast:
                ast_score = 0.0
            else:
                ast_score = res_ast["score"]
                # Cập nhật thống kê lỗi
                expl = res_ast["explanations"]
                if expl["tables"]["missing"]: missing_tables += 1
                if expl["filter_conditions"]["missing"]: missing_filters += 1
                if expl["join_conditions"]["missing"]: missing_joins += 1
            ast_scores.append(ast_score)
            
            if not gen_sql:
                print(f"[{qid}]: AI nộp giấy trắng (Trống) [AST: {ast_score * 100:.1f}%]")
                syntax_errors += 1
                continue
                
            # 1. Chạy code Đáp án (Ground Truth)
            try:
                df_gt = db.execute(gt_sql, timeout_sec=5.0)
            except Exception as e:
                print(f"[{qid}]: Lỗi ở code ĐÁP ÁN (Bỏ qua câu này): {e}")
                df_gt = None
                
            # 2. Chạy code AI viết
            try:
                df_gen = db.execute(gen_sql, timeout_sec=3.0)
            except duckdb.InterruptException:
                print(f"[{qid}]: TIMEOUT AI (Quá thời gian thực thi) [AST: {ast_score * 100:.1f}%]")
                syntax_errors += 1
                continue
            except Exception as e:
                print(f"[{qid}]: LỖI CÚ PHÁP AI [AST: {ast_score * 100:.1f}%]")
                syntax_errors += 1
                continue
                
            # 3. So sánh
            if df_gt is not None and df_gen is not None:
                if compare_results(df_gt, df_gen):
                    print(f"[{qid}]: ĐÚNG (Kết quả khớp 100%) [AST: {ast_score * 100:.1f}%]")
                    correct += 1
                else:
                    print(f"[{qid}]: SAI LOGIC [AST: {ast_score * 100:.1f}%]")
                    wrong_logic += 1
            else:
                wrong_logic += 1

    # ==========================================
    # IN BẢNG ĐIỂM
    # ==========================================
    print("\n" + "="*50)
    print("BẢNG ĐIỂM THỰC THI (EXECUTION ACCURACY)")
    print("="*50)
    print(f"Tổng số câu được chấm: {total}")
    if total > 0:
        print(f"✔️ Trả lời đúng (Khớp kết quả)  : {correct} câu ({(correct/total)*100:.2f}%)")
    print(f"Chạy được nhưng sai kết quả  : {wrong_logic} câu")
    print(f"Bị lỗi cú pháp / Không viết  : {syntax_errors} câu")
    print("="*50)

    # In kết quả AST Semantic Similarity
    avg_ast = sum(ast_scores) / len(ast_scores) if ast_scores else 0.0
    print("\n" + "="*50)
    print("BẢNG ĐIỂM TƯƠNG ĐỒNG NGỮ NGHĨA AST (AST SEMANTIC SIMILARITY)")
    print("="*50)
    print(f"✔️ Điểm tương đồng AST trung bình: {avg_ast * 100:.2f}%")
    print("-" * 50)
    print("Thống kê sự thiếu hụt logic của AI (AST Mismatches):")
    print(f"  + Số câu thiếu bảng cần dùng (Missing Tables)    : {missing_tables} câu")
    print(f"  + Số câu thiếu điều kiện lọc (Missing Filters)   : {missing_filters} câu")
    print(f"  + Số câu thiếu điều kiện kết nối (Missing Joins) : {missing_joins} câu")
    print("="*50)

    # Xuất bảng thống kê ra file kết quả Markdown
    correct_pct = (correct / total) * 100 if total > 0 else 0.0
    wrong_logic_pct = (wrong_logic / total) * 100 if total > 0 else 0.0
    syntax_errors_pct = (syntax_errors / total) * 100 if total > 0 else 0.0
    
    summary_md = f"""# BẢNG THỐNG KÊ KẾT QUẢ ĐÁNH GIÁ (EVALUATION SUMMARY REPORT)

Báo cáo thống kê kết quả thực thi và đánh giá tương đồng ngữ nghĩa AST của mô hình trên tập dữ liệu FloodSQL-Bench.

## 1. Bảng Điểm Thực Thi (Execution Accuracy)

| Chỉ số | Số lượng câu | Tỷ lệ (%) |
| :--- | :---: | :---: |
| ✔️ Trả lời đúng (Khớp kết quả) | {correct} | {correct_pct:.2f}% |
| ❌ Chạy được nhưng sai kết quả | {wrong_logic} | {wrong_logic_pct:.2f}% |
| ⚠️ Bị lỗi cú pháp / Không viết | {syntax_errors} | {syntax_errors_pct:.2f}% |
| **Tổng số câu được chấm** | **{total}** | **100.00%** |

## 2. Bảng Điểm Tương Đồng Ngữ Nghĩa AST (AST Semantic Similarity)

* **Điểm tương đồng AST trung bình**: **{avg_ast * 100:.2f}%**

### Thống kê sự thiếu hụt logic của AI (AST Mismatches):

| Loại thiếu hụt logic | Số câu bị thiếu |
| :--- | :---: |
| ❌ Thiếu bảng cần dùng (Missing Tables) | {missing_tables} |
| ❌ Thiếu điều kiện lọc (Missing Filters) | {missing_filters} |
| ❌ Thiếu điều kiện kết nối (Missing Joins) | {missing_joins} |
"""
    
    output_md_path = "results/eval_summary.md"
    os.makedirs(os.path.dirname(output_md_path), exist_ok=True)
    with open(output_md_path, "w", encoding="utf-8") as f_md:
        f_md.write(summary_md)
    print(f"\n[XUẤT FILE] Đã lưu bảng thống kê kết quả đánh giá tại: {output_md_path}")

if __name__ == "__main__":
    main()