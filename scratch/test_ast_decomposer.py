import sqlglot
from sqlglot import exp, parse_one

def resolve_aliases(expression):
    # Find all table aliases
    alias_map = {}
    for table in expression.find_all(exp.Table):
        if table.alias:
            alias_map[table.alias] = table.name
        else:
            alias_map[table.name] = table.name
            
    # Helper to resolve columns
    def transform(node):
        if isinstance(node, exp.Column):
            table_name = node.text("table")
            if table_name in alias_map:
                # Replace the table identifier with the actual table name
                node.set("table", exp.to_identifier(alias_map[table_name]))
        elif isinstance(node, exp.Table):
            # Remove table aliases to normalize table representation
            if node.alias:
                node.set("alias", None)
        return node

    return expression.transform(transform)

sql = "SELECT AVG(v.RPL_THEME1) AS avg_theme1_rank FROM svi v JOIN census_tracts t ON v.GEOID = t.GEOID JOIN floodplain f ON ST_Intersects(t.geometry, f.geometry) WHERE t.STATEFP='48';"
ast = parse_one(sql, read="duckdb")
print("Original SQL:", ast.sql())

normalized_ast = resolve_aliases(ast)
print("Normalized SQL (Aliases resolved):", normalized_ast.sql())
