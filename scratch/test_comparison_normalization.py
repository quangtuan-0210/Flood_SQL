import sqlglot
from sqlglot import exp, parse_one

def normalize_predicates(expression):
    def transform(node):
        # 1. Commutative comparisons: = and !=
        if isinstance(node, (exp.EQ, exp.NEQ)):
            left_sql = node.left.sql()
            right_sql = node.right.sql()
            if left_sql > right_sql:
                # Create a swapped node
                return node.__class__(this=node.args["expression"], expression=node.args["this"])
                
        # 2. Symmetric spatial functions: ST_Intersects, ST_Distance, ST_DWithin, ST_Touches, ST_Overlaps, ST_Crosses, ST_Equals
        elif isinstance(node, exp.Anonymous) and node.name.upper() in ["ST_INTERSECTS", "ST_DISTANCE", "ST_DWITHIN", "ST_TOUCHES", "ST_OVERLAPS", "ST_CROSSES", "ST_EQUALS"]:
            exprs = node.expressions
            if len(exprs) == 2:
                arg1_sql = exprs[0].sql()
                arg2_sql = exprs[1].sql()
                if arg1_sql > arg2_sql:
                    # Swap arguments
                    return exp.Anonymous(this=node.name, expressions=[exprs[1], exprs[0]])
                    
        # 3. Asymmetric spatial functions normalization: ST_Within(A, B) -> ST_Contains(B, A)
        elif isinstance(node, exp.Anonymous) and node.name.upper() == "ST_WITHIN":
            exprs = node.expressions
            if len(exprs) == 2:
                # Convert to ST_Contains(arg2, arg1)
                return exp.Anonymous(this="ST_Contains", expressions=[exprs[1], exprs[0]])
                
        return node
    return expression.transform(transform)

# Test cases
q1 = parse_one("SELECT * FROM t WHERE SVI.GEOID = CENSUS_TRACTS.GEOID AND ST_Intersects(t.geometry, f.geometry) AND ST_Within(t.geometry, f.geometry);")
print("Before:", q1.sql())
q1_norm = normalize_predicates(q1)
print("After :", q1_norm.sql())
