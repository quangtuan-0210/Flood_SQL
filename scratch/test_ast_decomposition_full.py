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

def flatten_and(expression):
    if expression is None:
        return []
    if isinstance(expression, exp.And):
        return flatten_and(expression.left) + flatten_and(expression.right)
    return [expression]

def get_tables(column_node):
    """Get all tables referenced in a column or sub-expression."""
    tables = set()
    for col in column_node.find_all(exp.Column):
        t = col.text("table")
        if t:
            tables.add(t)
    return tables

def decompose_query(sql_str):
    ast = parse_one(sql_str, read="duckdb")
    normalized_ast = resolve_aliases(ast)
    
    # 1. Tables (Sources)
    tables = {table.name for table in normalized_ast.find_all(exp.Table)}
    
    # 2. Select Expressions (Projections)
    select_exprs = []
    select_node = normalized_ast.args.get("expressions", [])
    for expr in select_node:
        # Strip alias for pure logic comparison
        if isinstance(expr, exp.Alias):
            select_exprs.append(expr.this.sql().upper())
        else:
            select_exprs.append(expr.sql().upper())
            
    # 3. Gather conditions from JOIN ON and WHERE
    all_predicates = []
    
    # From Joins
    joins = normalized_ast.args.get("joins", [])
    for join in joins:
        on_clause = join.args.get("on")
        if on_clause:
            all_predicates.extend(flatten_and(on_clause))
            
    # From Where
    where_node = normalized_ast.args.get("where")
    if where_node:
        all_predicates.extend(flatten_and(where_node.this))
        
    # Classify predicates into Join and Filter
    join_conditions = []
    filter_conditions = []
    
    for pred in all_predicates:
        referenced_tables = get_tables(pred)
        pred_sql = pred.sql().upper()
        if len(referenced_tables) > 1:
            join_conditions.append((referenced_tables, pred_sql))
        else:
            filter_conditions.append(pred_sql)
            
    # 4. Group by
    group_node = normalized_ast.args.get("group")
    group_by = [expr.sql().upper() for expr in group_node.expressions] if group_node else []
    
    # 5. Order by
    order_node = normalized_ast.args.get("order")
    order_by = [expr.sql().upper() for expr in order_node.expressions] if order_node else []
    
    # 6. Limit
    limit_node = normalized_ast.args.get("limit")
    limit = limit_node.sql().upper() if limit_node else None
    
    return {
        "tables": tables,
        "select": select_exprs,
        "join_conditions": join_conditions,
        "filter_conditions": filter_conditions,
        "group_by": group_by,
        "order_by": order_by,
        "limit": limit
    }

sql1 = "SELECT AVG(v.RPL_THEME1) AS avg_theme1_rank FROM svi v JOIN census_tracts t ON v.GEOID = t.GEOID JOIN floodplain f ON ST_Intersects(t.geometry, f.geometry) WHERE t.STATEFP='48' AND ST_IsValid(t.geometry);"
sql2 = "SELECT AVG(svi.RPL_THEME1) FROM census_tracts JOIN svi ON census_tracts.GEOID = svi.GEOID JOIN floodplain ON ST_Intersects(census_tracts.geometry, floodplain.geometry) WHERE census_tracts.STATEFP = '48';"

d1 = decompose_query(sql1)
d2 = decompose_query(sql2)

print("Query 1 Decomposed:")
for k, v in d1.items():
    print(f"  {k}: {v}")
    
print("\nQuery 2 Decomposed:")
for k, v in d2.items():
    print(f"  {k}: {v}")
