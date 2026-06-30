import sys
import os
import sqlglot
from sqlglot import exp, parse_one
from collections import Counter

# Đảm bảo đường dẫn import hoạt động
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from weighted_ast_similarity import resolve_aliases, normalize_predicates

def serialize_ast(node):
    """
    Tuần tự hóa đệ quy một nút SQLGlot AST thành dạng chuỗi canonical chuẩn hóa.
    """
    if node is None:
        return ""

    class_name = node.__class__.__name__
    label = class_name

    # Trích xuất giá trị cụ thể của một số nút để tăng độ chính xác so sánh
    if isinstance(node, (exp.Table, exp.Identifier, exp.Literal, exp.Var)):
        val = node.name if hasattr(node, "name") and node.name else (node.this if hasattr(node, "this") else "")
        if val:
            label = f"{class_name}:{val}"
    elif isinstance(node, exp.Anonymous):
        label = f"Func:{node.name.upper()}"
    elif isinstance(node, exp.Func) and hasattr(node, "name") and node.name:
        label = f"Func:{node.name.upper()}"

    # Thu thập chuỗi tuần tự hóa của các nút con
    child_strings = []
    for k, v in node.args.items():
        if v is None:
            continue
        if isinstance(v, list):
            for item in v:
                if isinstance(item, exp.Expression):
                    child_str = serialize_ast(item)
                    if child_str:
                        child_strings.append(child_str)
        elif isinstance(v, exp.Expression):
            child_str = serialize_ast(v)
            if child_str:
                child_strings.append(child_str)

    if child_strings:
        return f"{label}({','.join(child_strings)})"
    return label

def get_all_subtrees(node):
    """
    Trích xuất toàn bộ danh sách các cây con (dưới dạng chuỗi canonical) từ nút hiện tại và tất cả các con.
    """
    if node is None:
        return []
        
    subtrees = [serialize_ast(node)]
    for k, v in node.args.items():
        if v is None:
            continue
        if isinstance(v, list):
            for item in v:
                if isinstance(item, exp.Expression):
                    subtrees.extend(get_all_subtrees(item))
        elif isinstance(v, exp.Expression):
            subtrees.extend(get_all_subtrees(v))
    return subtrees

def calculate_subtree_matching_similarity(sql1, sql2):
    """
    Tính toán độ tương đồng Jaccard trên tập đa hợp các cây con (subtrees) giữa hai câu SQL.
    Trả về một dictionary chứa score và thông tin chi tiết.
    """
    if not sql1 or not sql2:
        return {"score": 0.0, "matches_count": 0, "size1": 0, "size2": 0, "matching_subtrees": []}

    try:
        ast1 = parse_one(sql1, read="duckdb")
        ast1 = resolve_aliases(ast1)
        ast1 = normalize_predicates(ast1)
        subtrees1 = get_all_subtrees(ast1)
    except Exception:
        subtrees1 = []

    try:
        ast2 = parse_one(sql2, read="duckdb")
        ast2 = resolve_aliases(ast2)
        ast2 = normalize_predicates(ast2)
        subtrees2 = get_all_subtrees(ast2)
    except Exception:
        subtrees2 = []

    size1 = len(subtrees1)
    size2 = len(subtrees2)

    if size1 == 0 and size2 == 0:
        return {"score": 1.0, "matches_count": 0, "size1": 0, "size2": 0, "matching_subtrees": []}
    if size1 == 0 or size2 == 0:
        return {"score": 0.0, "matches_count": 0, "size1": size1, "size2": size2, "matching_subtrees": []}

    # Tính giao của hai tập đa hợp (Counter intersection)
    c1 = Counter(subtrees1)
    c2 = Counter(subtrees2)
    intersection = c1 & c2
    
    matches_count = sum(intersection.values())
    union_count = size1 + size2 - matches_count
    
    if union_count == 0:
        score = 1.0
    else:
        score = matches_count / union_count

    # Lấy danh sách các cây con trùng khớp (sắp xếp theo độ dài chuỗi giảm dần để lấy các cây con lớn trước)
    matching_subtrees = []
    for item, count in intersection.items():
        matching_subtrees.append({"subtree": item, "count": count})
    matching_subtrees.sort(key=lambda x: len(x["subtree"]), reverse=True)

    return {
        "score": score,
        "matches_count": matches_count,
        "size1": size1,
        "size2": size2,
        "matching_subtrees": matching_subtrees
    }
