import sys
import os
import sqlglot
from sqlglot import exp, parse_one
import zss
from zss import Node, simple_distance

# Đảm bảo đường dẫn import hoạt động
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from weighted_ast_similarity import resolve_aliases, normalize_predicates

def sql_to_zss_tree(sql_str):
    """
    Chuyển đổi truy vấn SQL thành cây đối tượng zss.Node đã chuẩn hóa.
    Nếu có lỗi cú pháp hoặc SQL trống, trả về None.
    """
    if not sql_str:
        return None
    try:
        ast = parse_one(sql_str, read="duckdb")
    except Exception:
        return None

    # Chuẩn hóa cây AST
    ast = resolve_aliases(ast)
    ast = normalize_predicates(ast)

    return _ast_to_zss(ast)

def _ast_to_zss(node):
    """
    Chuyển đổi đệ quy một nút SQLGlot AST thành zss.Node.
    """
    if node is None:
        return None

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

    zss_node = Node(label)

    # Duyệt qua các nút con của SQLGlot AST
    for k, v in node.args.items():
        if v is None:
            continue
        if isinstance(v, list):
            for item in v:
                if isinstance(item, exp.Expression):
                    child_zss = _ast_to_zss(item)
                    if child_zss:
                        zss_node.addkid(child_zss)
        elif isinstance(v, exp.Expression):
            child_zss = _ast_to_zss(v)
            if child_zss:
                zss_node.addkid(child_zss)

    return zss_node

def count_nodes(node):
    """
    Đếm tổng số nút trong một cây zss.Node.
    """
    if node is None:
        return 0
    return 1 + sum(count_nodes(child) for child in node.children)

def calculate_tree_edit_distance_similarity(sql1, sql2):
    """
    Tính điểm tương đồng giữa 2 truy vấn SQL dựa trên Tree Edit Distance.
    Trả về một dictionary chứa score và các thông số phụ.
    """
    t1 = sql_to_zss_tree(sql1)
    t2 = sql_to_zss_tree(sql2)

    if t1 is None and t2 is None:
        return {"score": 1.0, "distance": 0, "size1": 0, "size2": 0}
    
    size1 = count_nodes(t1) if t1 is not None else 0
    size2 = count_nodes(t2) if t2 is not None else 0
    
    if t1 is None or t2 is None:
        max_size = max(size1, size2)
        return {"score": 0.0, "distance": max_size, "size1": size1, "size2": size2}

    dist = simple_distance(t1, t2)
    max_dist = size1 + size2

    if max_dist == 0:
        score = 1.0
    else:
        score = 1.0 - (dist / max_dist)

    return {
        "score": score,
        "distance": dist,
        "size1": size1,
        "size2": size2
    }
