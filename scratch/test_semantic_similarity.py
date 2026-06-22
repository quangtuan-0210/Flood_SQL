import sqlglot
from sqlglot import exp, parse_one

def resolve_aliases(expression):
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
    def transform(node):
        # 1. Commutative comparisons: = and !=
        if isinstance(node, (exp.EQ, exp.NEQ)):
            left_sql = node.left.sql().upper()
            right_sql = node.right.sql().upper()
            if left_sql > right_sql:
                return node.__class__(this=node.args["expression"], expression=node.args["this"])
                
        # 2. Symmetric spatial functions
        elif isinstance(node, exp.Anonymous) and node.name.upper() in ["ST_INTERSECTS", "ST_DISTANCE", "ST_DWITHIN", "ST_TOUCHES", "ST_OVERLAPS", "ST_CROSSES", "ST_EQUALS"]:
            exprs = node.expressions
            if len(exprs) == 2:
                arg1_sql = exprs[0].sql().upper()
                arg2_sql = exprs[1].sql().upper()
                if arg1_sql > arg2_sql:
                    return exp.Anonymous(this=node.name, expressions=[exprs[1], exprs[0]])
                    
        # 3. Asymmetric spatial functions: ST_Within(A, B) -> ST_Contains(B, A)
        elif isinstance(node, exp.Anonymous) and node.name.upper() == "ST_WITHIN":
            exprs = node.expressions
            if len(exprs) == 2:
                return exp.Anonymous(this="ST_Contains", expressions=[exprs[1], exprs[0]])
                
        return node
    return expression.transform(transform)

def flatten_and(expression):
    if expression is None:
        return []
    if isinstance(expression, exp.And):
        return flatten_and(expression.left) + flatten_and(expression.right)
    return [expression]

def get_tables(column_node):
    tables = set()
    for col in column_node.find_all(exp.Column):
        t = col.text("table")
        if t:
            tables.add(t)
    return tables

def decompose_query(sql_str):
    try:
        ast = parse_one(sql_str, read="duckdb")
    except Exception as e:
        # If parsing fails, return None or empty structure
        return None
        
    normalized_ast = resolve_aliases(ast)
    normalized_ast = normalize_predicates(normalized_ast)
    
    # 1. Tables
    tables = {table.name for table in normalized_ast.find_all(exp.Table)}
    
    # 2. Select
    select_exprs = []
    select_node = normalized_ast.args.get("expressions", [])
    for expr in select_node:
        if isinstance(expr, exp.Alias):
            select_exprs.append(expr.this.sql().upper())
        else:
            select_exprs.append(expr.sql().upper())
            
    # 3. Join and Filter conditions
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
    
    for pred in all_predicates:
        referenced_tables = get_tables(pred)
        pred_sql = pred.sql().upper()
        if len(referenced_tables) > 1:
            join_conditions.add(pred_sql)
        else:
            filter_conditions.add(pred_sql)
            
    # 4. Group by
    group_node = normalized_ast.args.get("group")
    group_by = {expr.sql().upper() for expr in group_node.expressions} if group_node else set()
    
    # 5. Order by
    order_node = normalized_ast.args.get("order")
    order_by = {expr.sql().upper() for expr in order_node.expressions} if order_node else set()
    
    # 6. Limit
    limit_node = normalized_ast.args.get("limit")
    limit = limit_node.sql().upper() if limit_node else None
    
    return {
        "tables": tables,
        "select": set(select_exprs),
        "join_conditions": join_conditions,
        "filter_conditions": filter_conditions,
        "group_by": group_by,
        "order_by": order_by,
        "limit": limit
    }

def calculate_jaccard(set1, set2):
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))

def compare_queries(gt_sql, pred_sql):
    d_gt = decompose_query(gt_sql)
    d_pred = decompose_query(pred_sql)
    
    if d_gt is None or d_pred is None:
        # Parsing error
        return {
            "score": 0.0,
            "error": "Lỗi phân tích cú pháp SQL (Syntax Error) ở một trong hai truy vấn."
        }
        
    components = ["tables", "select", "join_conditions", "filter_conditions", "group_by", "order_by"]
    weights = {
        "tables": 0.15,
        "select": 0.20,
        "join_conditions": 0.25,
        "filter_conditions": 0.25,
        "group_by": 0.05,
        "order_by": 0.05,
        "limit": 0.05
    }
    
    scores = {}
    explanations = {}
    
    for comp in components:
        set_gt = d_gt[comp]
        set_pred = d_pred[comp]
        scores[comp] = calculate_jaccard(set_gt, set_pred)
        
        # Determine matches, missing, extra
        matches = set_gt.intersection(set_pred)
        missing = set_gt - set_pred
        extra = set_pred - set_gt
        
        explanations[comp] = {
            "matches": list(matches),
            "missing": list(missing),
            "extra": list(extra)
        }
        
    # Handle limit separately (scalar value)
    limit_gt = d_gt["limit"]
    limit_pred = d_pred["limit"]
    if limit_gt == limit_pred:
        scores["limit"] = 1.0
        explanations["limit"] = {"status": "Khớp", "gt": limit_gt, "pred": limit_pred}
    else:
        scores["limit"] = 0.0
        explanations["limit"] = {"status": "Khác biệt", "gt": limit_gt, "pred": limit_pred}
        
    # Calculate overall weighted score
    overall_score = sum(scores[comp] * weights[comp] for comp in weights)
    
    return {
        "score": overall_score,
        "component_scores": scores,
        "explanations": explanations
    }

# Test the similarity module
gt = "SELECT AVG(v.RPL_THEME1) AS avg_theme1_rank FROM svi v JOIN census_tracts t ON v.GEOID = t.GEOID JOIN floodplain f ON ST_Intersects(t.geometry, f.geometry) WHERE t.STATEFP='48' AND ST_IsValid(t.geometry);"
pred = "SELECT AVG(svi.RPL_THEME1) FROM census_tracts JOIN svi ON census_tracts.GEOID = svi.GEOID JOIN floodplain ON ST_Intersects(census_tracts.geometry, floodplain.geometry) WHERE census_tracts.STATEFP = '48';"

result = compare_queries(gt, pred)
print("Weighted Score:", result["score"])
print("Component Scores:")
for k, v in result["component_scores"].items():
    print(f"  {k}: {v}")
print("\nExplanations:")
import json
print(json.dumps(result["explanations"], indent=2))
