import os
import time
import contextlib
import logging

DATABASE_URL = os.getenv("DATABASE_URL")
IS_PG = DATABASE_URL and DATABASE_URL.startswith("postgres")

_pg_pool = None

def get_pg_pool():
    global _pg_pool
    if _pg_pool is None and IS_PG:
        import psycopg2
        from psycopg2.pool import SimpleConnectionPool
        
        # Render internal DNS might take a few seconds to resolve newly created databases
        retries = 10
        while retries > 0:
            try:
                _pg_pool = SimpleConnectionPool(1, 20, DATABASE_URL)
                break
            except psycopg2.OperationalError as e:
                logging.warning(f"[!] PostgreSQL not ready yet, retrying in 5 seconds... ({e})")
                time.sleep(5)
                retries -= 1
        
        if _pg_pool is None:
            raise Exception("Failed to connect to PostgreSQL after multiple retries. Please check DATABASE_URL.")
            
    return _pg_pool

@contextlib.contextmanager
def get_db(db_path):
    if IS_PG:
        pool = get_pg_pool()
        conn = pool.getconn()
        wrapper = PGConnectionWrapper(conn)
        try:
            yield wrapper
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            wrapper.close()
            pool.putconn(conn)
    else:
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        wrapper = SQLiteConnectionWrapper(conn)
        try:
            yield wrapper
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            wrapper.close()
            conn.close()

class SQLiteConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()
    def cursor(self):
        return self
    def execute(self, query, params=()):
        self.cur.execute(query, params)
        return self
    def fetchone(self):
        return self.cur.fetchone()
    def fetchall(self):
        return self.cur.fetchall()
    @property
    def lastrowid(self):
        return self.cur.lastrowid
    def close(self):
        self.cur.close()
    def commit(self):
        self.conn.commit()

class PGConnectionWrapper:
    def __init__(self, conn):
        from psycopg2.extras import DictCursor
        self.conn = conn
        self.cur = conn.cursor(cursor_factory=DictCursor)
    def cursor(self):
        return self
    def execute(self, query, params=()):
        q = query.replace("?", "%s")
        q = q.replace("AUTOINCREMENT", "SERIAL")
        self.cur.execute(q, params)
        return self
    def fetchone(self):
        return self.cur.fetchone()
    def fetchall(self):
        return self.cur.fetchall()
    @property
    def lastrowid(self):
        self.cur.execute("SELECT lastval()")
        return self.cur.fetchone()[0]
    def close(self):
        self.cur.close()
    def commit(self):
        self.conn.commit()
