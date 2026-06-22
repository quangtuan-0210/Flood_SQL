import os
import glob
import duckdb
import pandas as pd
from multiprocessing import Process, Queue

def run_query_worker(sql, queue):
    try:
        con = duckdb.connect(database=':memory:')
        con.execute("INSTALL spatial;")
        con.execute("LOAD spatial;")
        for filepath in glob.glob(os.path.join("data", "*.parquet")):
            filename = os.path.basename(filepath)
            table_name = filename.replace('.parquet', '').replace('_tx_fl_la', '')
            con.execute(f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM '{filepath}'")
            
        df = con.execute(sql).fetchdf()
        queue.put((True, df))
    except Exception as e:
        queue.put((False, str(e)))

def execute_with_timeout(sql, timeout_sec=3.0):
    queue = Queue()
    p = Process(target=run_query_worker, args=(sql, queue))
    p.start()
    p.join(timeout=timeout_sec)
    if p.is_alive():
        p.terminate()
        p.join()
        return None  # Timeout
    if not queue.empty():
        success, res = queue.get()
        if success:
            return res
        else:
            print("Worker error:", res)
    return None

if __name__ == "__main__":
    import time
    print("Testing sequential execution time...")
    t0 = time.time()
    queue = Queue()
    run_query_worker("SELECT 1 AS val;", queue)
    t1 = time.time()
    print(f"Sequential run took {t1 - t0:.2f} seconds.")
    if not queue.empty():
        success, res = queue.get()
        print("Sequential result success:", success, "res:", res)
        
    print("\nTesting fast query with timeout...")
    df = execute_with_timeout("SELECT 1 AS val;", timeout_sec=10.0)
    if df is not None:
        print("Fast query success:", df)
    else:
        print("Fast query failed/timeout")

    print("\nTesting slow/hanging query...")
    # A slow cross join to simulate hang
    slow_sql = "SELECT * FROM (SELECT range AS a FROM range(1000000)) t1 JOIN (SELECT range AS b FROM range(1000000)) t2 ON t1.a <> t2.b LIMIT 10;"
    df_slow = execute_with_timeout(slow_sql, timeout_sec=2.0)
    if df_slow is None:
        print("Slow query timed out successfully!")
    else:
        print("Slow query finished:", df_slow)
