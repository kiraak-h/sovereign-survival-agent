import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'sniper_wallets.db')

def update_limit_orders_schema():
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute('ALTER TABLE limit_orders ADD COLUMN entry_price REAL DEFAULT 0.0')
        except sqlite3.OperationalError:
            pass # Column likely already exists

update_limit_orders_schema()
