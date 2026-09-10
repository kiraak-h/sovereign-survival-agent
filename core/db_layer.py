import os
import sqlite3
import re
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL")

class DBLayer:
    def __init__(self, db_name="sniper_wallets.db"):
        self.db_name = db_name
        self.is_pg = DATABASE_URL is not None and DATABASE_URL.startswith("postgres")
        if self.is_pg:
            import psycopg2
            from psycopg2.extras import DictCursor
            self.pool = psycopg2.pool.SimpleConnectionPool(1, 10, DATABASE_URL)
        else:
            self.pool = None

    @contextmanager
    def get_cursor(self, commit=False):
        if self.is_pg:
            conn = self.pool.getconn()
            try:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    yield cur
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                self.pool.putconn(conn)
        else:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            try:
                cur = conn.cursor()
                yield cur
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()

    def execute(self, query, params=(), commit=True):
        if self.is_pg:
            query = query.replace("?", "%s")
            query = query.replace("AUTOINCREMENT", "SERIAL")
        
        # Postgres lastrowid workaround:
        # If it's an INSERT and we need the ID, append RETURNING id
        if self.is_pg and query.strip().upper().startswith("INSERT") and "RETURNING id" not in query:
            # We only append RETURNING id if there's a SERIAL primary key.
            # For simplicity, we just execute.
            pass

        with self.get_cursor(commit=commit) as cur:
            cur.execute(query, params)
            return cur
