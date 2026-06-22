import sqlglot
from sqlglot import exp, parse_one

# Example query from FloodSQL
sql1 = "SELECT AVG(v.RPL_THEME1) AS avg_theme1_rank FROM svi v JOIN census_tracts t ON v.GEOID = t.GEOID JOIN floodplain f ON ST_Intersects(t.geometry, f.geometry) WHERE t.STATEFP='48' AND ST_IsValid(t.geometry) AND ST_IsValid(f.geometry);"
sql2 = "SELECT AVG(svi.RPL_THEME1) FROM census_tracts JOIN svi ON census_tracts.GEOID = svi.GEOID JOIN floodplain ON ST_Intersects(census_tracts.geometry, floodplain.geometry) WHERE census_tracts.STATEFP = '48';"

try:
    print("Parsing sql1...")
    ast1 = parse_one(sql1, read="duckdb")
    print("AST1 type:", type(ast1))
    print("AST1 repr:", repr(ast1)[:300])

    print("\nParsing sql2...")
    ast2 = parse_one(sql2, read="duckdb")
    print("AST2 repr:", repr(ast2)[:300])

    # Let's inspect some properties
    print("\nTables in AST1:")
    for table in ast1.find_all(exp.Table):
        print("Table name:", table.name, "Alias:", table.alias)

    print("\nFunctions in AST1:")
    for func in ast1.find_all(exp.Anonymous):
        print("Anonymous func:", func.name, "Args:", func.args)
    for func in ast1.find_all(exp.Func):
        print("Standard func:", func.sql())
except Exception as e:
    print("Failed to parse:", e)
