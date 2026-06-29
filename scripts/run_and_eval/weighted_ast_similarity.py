import os
import json
import argparse
import numpy as np
import sqlglot
from sqlglot import exp, parse_one

def resolve_aliases(expression):
    """
    Quy đổi toàn bộ bí danh bảng (aliases) về tên gốc của bảng trong các tham chiếu cột.
    Gỡ bỏ bí danh của các bảng trong mệnh đề FROM/JOIN.
    """
    alias_map = {}
    for table in expression.find_all(exp.Table):
        if table.alias:
            alias_map[table.alias] = table.name
        else:
            alias_map[table.name] = table.name
            
    def transform(node):
        if isinstance(node, exp.Column):
            table_name = node.text("table")
            if table_name in alias_map:
                node.set("table", exp.to_identifier(alias_map[table_name]))
        elif isinstance(node, exp.Table):
            if node.alias:
                node.set("alias", None)
        return node

    return expression.transform(transform)

def normalize_predicates(expression):
    """
    Chuẩn hóa các mệnh đề điều kiện trong AST:
    1. So sánh giao hoán (=, !=): sắp xếp hai toán hạng theo thứ tự chữ cái.
    2. Hàm không gian đối xứng (ST_Intersects, ST_Distance, ...): sắp xếp tham số theo chữ cái.
    3. Hàm không gian bất đối xứng (ST_Within): chuyển đổi ST_Within(A, B) thành ST_Contains(B, A).
    """
    def transform(node):
        # 1. So sánh giao hoán (=, !=)
        if isinstance(node, (exp.EQ, exp.NEQ)):
            left_sql = node.left.sql().upper()
            right_sql = node.right.sql().upper()
            if left_sql > right_sql:
                return node.__class__(this=node.args["expression"], expression=node.args["this"])
                
        # 2. Hàm không gian đối xứng
        elif isinstance(node, exp.Anonymous) and node.name.upper() in [
            "ST_INTERSECTS", "ST_DISTANCE", "ST_DWITHIN", "ST_TOUCHES", 
            "ST_OVERLAPS", "ST_CROSSES", "ST_EQUALS"
        ]:
            exprs = node.expressions
            if len(exprs) == 2:
                arg1_sql = exprs[0].sql().upper()
                arg2_sql = exprs[1].sql().upper()
                if arg1_sql > arg2_sql:
                    return exp.Anonymous(this=node.name, expressions=[exprs[1], exprs[0]])
                    
        # 3. Hàm không gian bất đối xứng: ST_Within(A, B) -> ST_Contains(B, A)
        elif isinstance(node, exp.Anonymous) and node.name.upper() == "ST_WITHIN":
            exprs = node.expressions
            if len(exprs) == 2:
                return exp.Anonymous(this="ST_Contains", expressions=[exprs[1], exprs[0]])
                
        return node
    return expression.transform(transform)

def flatten_and(expression):
    """
    Phẳng hóa các cấu trúc điều kiện kết hợp bởi toán tử AND để dễ so sánh.
    """
    if expression is None:
        return []
    if isinstance(expression, exp.And):
        return flatten_and(expression.left) + flatten_and(expression.right)
    return [expression]

def get_tables(column_node):
    """
    Lấy danh sách các bảng được tham chiếu trong một nút/biểu thức cột.
    """
    tables = set()
    for col in column_node.find_all(exp.Column):
        t = col.text("table")
        if t:
            tables.add(t)
    return tables

def decompose_query(sql_str):
    """
    Phân tích một câu SQL và tách thành các thành phần chuẩn hóa theo hệ trọng số mới:
    - spatial_functions: các hàm không gian bắt đầu bằng ST_
    - select: các cột/biểu thức đầu ra trong SELECT (không có alias AS)
    - where: các điều kiện lọc đơn bảng
    - from: các bảng sử dụng (tables)
    - join: các điều kiện kết nối liên bảng (join conditions)
    - predicate: các vị từ so sánh thuộc tính phi không gian
    - group_by: các trường gom nhóm
    - order_by: các trường sắp xếp
    - limit: giới hạn số lượng bản ghi
    """
    if not sql_str:
        return None
        
    try:
        ast = parse_one(sql_str, read="duckdb")
    except Exception:
        return None
        
    # Chuẩn hóa AST
    normalized_ast = resolve_aliases(ast)
    normalized_ast = normalize_predicates(normalized_ast)
    
    # 1. Trích xuất Spatial Functions (30%)
    spatial_funcs = set()
    for node in normalized_ast.find_all((exp.Func, exp.Anonymous)):
        name = node.name if hasattr(node, "name") else node.__class__.__name__
        if name.upper().startswith("ST_"):
            spatial_funcs.add(node.sql().upper())
            
    # 2. Trích xuất Select Expressions (15%)
    select_exprs = []
    select_node = normalized_ast.args.get("expressions", [])
    for expr in select_node:
        if isinstance(expr, exp.Alias):
            select_exprs.append(expr.this.sql().upper())
        else:
            select_exprs.append(expr.sql().upper())
            
    # 3. Trích xuất các điều kiện từ mệnh đề JOIN ON và WHERE
    all_predicates = []
    joins = normalized_ast.args.get("joins", [])
    for join in joins:
        on_clause = join.args.get("on")
        if on_clause:
            all_predicates.extend(flatten_and(on_clause))
            
    where_node = normalized_ast.args.get("where")
    if where_node:
        all_predicates.extend(flatten_and(where_node.this))
        
    join_conditions = set()
    filter_conditions = set()
    non_spatial_predicates = set()
    
    for pred in all_predicates:
        referenced_tables = get_tables(pred)
        pred_sql = pred.sql().upper()
        
        # Phân loại Join / Filter
        if len(referenced_tables) > 1:
            join_conditions.add(pred_sql)
        else:
            filter_conditions.add(pred_sql)
            
        # Vị từ phi không gian (Predicate - 10%)
        if "ST_" not in pred_sql:
            non_spatial_predicates.add(pred_sql)
            
    # 4. Trích xuất Tables (FROM - 10%)
    tables = {table.name.lower() for table in normalized_ast.find_all(exp.Table)}
    
    # 5. Trích xuất GROUP BY (5%)
    group_node = normalized_ast.args.get("group")
    group_by = {expr.sql().upper() for expr in group_node.expressions} if group_node else set()
    
    # 6. Trích xuất ORDER BY (5%)
    order_node = normalized_ast.args.get("order")
    order_by = {expr.sql().upper() for expr in order_node.expressions} if order_node else set()
    
    # 7. Trích xuất LIMIT
    limit_node = normalized_ast.args.get("limit")
    limit = limit_node.sql().upper() if limit_node else None
    
    return {
        "spatial_functions": spatial_funcs,
        "select": set(select_exprs),
        "where": filter_conditions,
        "from": tables,
        "join": join_conditions,
        "predicate": non_spatial_predicates,
        "group_by": group_by,
        "order_by": order_by,
        "limit": limit
    }

def calculate_jaccard(set1, set2):
    """
    Tính chỉ số tương đồng Jaccard giữa hai tập hợp.
    """
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))

def compare_queries(gt_sql, pred_sql):
    """
    So sánh hai câu SQL (Ground Truth và Predicted) dựa trên AST.
    Trả về điểm tương đồng tổng hợp theo phân bổ trọng số mới.
    """
    d_gt = decompose_query(gt_sql)
    d_pred = decompose_query(pred_sql)
    
    if d_gt is None:
        return {
            "score": 0.0,
            "error": "Lỗi cú pháp SQL trong câu Ground Truth."
        }
    if d_pred is None:
        return {
            "score": 0.0,
            "error": "Lỗi cú pháp SQL trong câu Predicted (AI sinh ra)."
        }
        
    components = ["spatial_functions", "select", "where", "from", "join", "predicate", "group_by", "order_by"]
    weights = {
        "spatial_functions": 0.30,
        "select": 0.15,
        "where": 0.15,
        "from": 0.10,
        "join": 0.10,
        "predicate": 0.10,
        "group_by": 0.05,
        "order_by": 0.05
    }
    
    scores = {}
    explanations = {}
    
    for comp in components:
        set_gt = d_gt[comp]
        set_pred = d_pred[comp]
        scores[comp] = calculate_jaccard(set_gt, set_pred)
        
        matches = set_gt.intersection(set_pred)
        missing = set_gt - set_pred
        extra = set_pred - set_gt
        
        explanations[comp] = {
            "matches": list(matches),
            "missing": list(missing),
            "extra": list(extra)
        }
        
    # Copy các key cũ để tương thích ngược với eval.py và generate_report.py
    explanations["tables"] = explanations["from"]
    explanations["filter_conditions"] = explanations["where"]
    explanations["join_conditions"] = explanations["join"]
    
    # So sánh Limit riêng biệt
    limit_gt = d_gt["limit"]
    limit_pred = d_pred["limit"]
    if limit_gt == limit_pred:
        scores["limit"] = 1.0
        explanations["limit"] = {"status": "Khớp", "gt": limit_gt, "pred": limit_pred}
    else:
        scores["limit"] = 0.0
        explanations["limit"] = {"status": "Khác biệt", "gt": limit_gt, "pred": limit_pred}
        
    # Tính điểm trung bình có trọng số
    overall_score = sum(scores[comp] * weights[comp] for comp in weights)
    
    return {
        "score": overall_score,
        "component_scores": scores,
        "explanations": explanations
    }

def run_semantic_eval_file(input_file):
    """
    Đọc tệp kết quả JSONL chứa truy vấn GT và Predicted, đánh giá tương đồng ngữ nghĩa.
    In ra báo cáo tổng hợp.
    """
    if not os.path.exists(input_file):
        print(f"[ERROR] Không tìm thấy file kết quả tại '{input_file}'!")
        return
        
    scores = []
    syntax_errors = 0
    total = 0
    
    # Thống kê chi tiết
    missing_tables_count = 0
    missing_filters_count = 0
    missing_joins_count = 0
    extra_tables_count = 0
    
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
            except Exception:
                continue
                
            total += 1
            gt_sql = record.get("gt_sql") or record.get("sql")
            pred_sql = record.get("generated_sql")
            qid = record.get("id", f"Q_{total}")
            
            res = compare_queries(gt_sql, pred_sql)
            
            if "error" in res:
                syntax_errors += 1
                scores.append(0.0)
            else:
                score = res["score"]
                scores.append(score)
                
                # Cập nhật thống kê lỗi
                expl = res["explanations"]
                if expl["tables"]["missing"]: missing_tables_count += 1
                if expl["tables"]["extra"]: extra_tables_count += 1
                if expl["filter_conditions"]["missing"]: missing_filters_count += 1
                if expl["join_conditions"]["missing"]: missing_joins_count += 1
                
    avg_score = np.mean(scores) if scores else 0.0
    
    print("\n" + "=" * 60)
    print("BÁO CÁO TƯƠNG ĐỒNG NGỮ NGHĨA AST (AST SEMANTIC SIMILARITY)")
    print("=" * 60)
    print(f"Tổng số câu đánh giá: {total}")
    print(f"Điểm tương đồng ngữ nghĩa trung bình (AST Score): {avg_score * 100:.2f}%")
    print(f"Số câu bị lỗi cú pháp phía AI (Syntax Errors)  : {syntax_errors} câu ({(syntax_errors/total)*100 if total > 0 else 0:.2f}%)")
    print("-" * 60)
    print("Thống kê sự thiếu hụt logic của AI (Mismatches):")
    print(f"  + Số câu thiếu bảng cần dùng (Missing Tables)    : {missing_tables_count} câu")
    print(f"  + Số câu thừa bảng không cần dùng (Extra Tables) : {extra_tables_count} câu")
    print(f"  + Số câu thiếu điều kiện lọc (Missing Filters)   : {missing_filters_count} câu")
    print(f"  + Số câu thiếu điều kiện kết nối (Missing Joins) : {missing_joins_count} câu")
    print("=" * 60 + "\n")
    
    return avg_score

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Đánh giá tương đồng ngữ nghĩa SQL dựa trên cây AST.")
    parser.add_argument("--input", type=str, required=True, help="Đường dẫn tới file kết quả .jsonl")
    args = parser.parse_args()
    run_semantic_eval_file(args.input)
