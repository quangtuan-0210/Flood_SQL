import sys
import os
import sqlglot
from sqlglot import parse_one

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts", "run_and_eval"))
from semantic_similarity import resolve_aliases, normalize_predicates

def format_ast_tree(node, indent=0):
    if node is None:
        return ""
    lines = []
    node_name = node.__class__.__name__
    lines.append("  " * indent + f"└─ {node_name}")
    for k, v in node.args.items():
        if v is None:
            continue
        if isinstance(v, list):
            for item in v:
                if isinstance(item, sqlglot.Expression):
                    lines.append(format_ast_tree(item, indent + 1))
        elif isinstance(v, sqlglot.Expression):
            lines.append(format_ast_tree(v, indent + 1))
    return "\n".join(lines)

sql = "SELECT COUNT(*) AS num_claims FROM claims WHERE GEOID LIKE '48201%' AND dateOfLoss >= DATE '2010-01-01';"
try:
    ast = parse_one(sql, read="duckdb")
    normalized = resolve_aliases(ast)
    normalized = normalize_predicates(normalized)
    tree = format_ast_tree(normalized)
    print("Success!")
    print(tree)
except Exception as e:
    import traceback
    print("Failed with exception:", e)
    traceback.print_exc()
