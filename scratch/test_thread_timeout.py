import os
import glob
import duckdb
import pandas as pd
import threading
import time

class TimeoutConnection:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.con = self._init_db()

    def _init_db(self):
        con = duckdb.connect(database=':memory:')
        con.execute("INSTALL spatial;")
        con.execute("LOAD spatial;")
        for filepath in glob.glob(os.path.join(self.data_dir, "*.parquet")):
            filename = os.path.basename(filepath)
            table_name = filename.replace('.parquet', '').replace('_tx_fl_la', '')
            con.execute(f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM '{filepath}'")
        return con

    def execute(self, sql, timeout_sec=3.0):
        interrupted = False
        def interrupt_func():
            nonlocal interrupted
            interrupted = True
            try:
                self.con.interrupt()
            except Exception:
                pass

        timer = threading.Timer(timeout_sec, interrupt_func)
        try:
            timer.start()
            df = self.con.execute(sql).fetchdf()
            if interrupted:
                raise duckdb.InterruptException("Query timed out")
            return df
        except duckdb.InterruptException:
            try:
                self.con.close()
            except Exception:
                pass
            self.con = self._init_db()
            raise
        finally:
            timer.cancel()

if __name__ == "__main__":
    print("Initializing TimeoutConnection...")
    db = TimeoutConnection()
    
    print("\nTesting fast query...")
    t0 = time.time()
    df = db.execute("SELECT 1 AS val;", timeout_sec=2.0)
    print(f"Fast query took {time.time() - t0:.4f}s. Result:\n", df)

    print("\nTesting slow query...")
    t0 = time.time()
    slow_sql = "SELECT COUNT(*) FROM (SELECT range AS a FROM range(10000000)) t1 JOIN (SELECT range AS b FROM range(10000000)) t2 ON t1.a <> t2.b;"
    try:
        df_slow = db.execute(slow_sql, timeout_sec=1.5)
        print("Slow query result:\n", df_slow)
    except duckdb.InterruptException:
        print("Successfully timed out slow query!")
    print(f"Slow query took {time.time() - t0:.4f}s.")

    print("\nTesting subsequent fast query after timeout...")
    t0 = time.time()
    df_next = db.execute("SELECT 2 AS val;", timeout_sec=2.0)
    print(f"Subsequent fast query took {time.time() - t0:.4f}s. Result:\n", df_next)

