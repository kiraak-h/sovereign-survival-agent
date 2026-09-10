import os
import contextlib

DATABASE_URL = os.getenv("DATABASE_URL")
IS_PG = DATABASE_URL and DATABASE_URL.startswith("postgres")

if IS_PG:
    import psycopg2
    from psycopg2.extras import DictCursor
    from psycopg2.pool import SimpleConnectionPool
    pg_pool = SimpleConnectionPool(1, 20, DATABASE_URL)
else:
    import sqlite3

@contextlib.contextmanager
def get_db(db_path):
    if IS_PG:
        conn = pg_pool.getconn()
        wrapper = PGConnectionWrapper(conn)
        try:
            yield wrapper
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            wrapper.close()
            pg_pool.putconn(conn)
    else:
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
