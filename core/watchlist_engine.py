import time
import random
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'sniper_wallets.db')

def init_watchlist_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            token_address TEXT NOT NULL,
            symbol TEXT,
            target_price_usd REAL NOT NULL,
            direction TEXT DEFAULT 'ABOVE',
            status TEXT DEFAULT 'ACTIVE'
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS tx_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            token_address TEXT NOT NULL,
            action TEXT NOT NULL,
            eth_amount REAL,
            tx_hash TEXT,
            timestamp REAL,
            pnl_pct REAL DEFAULT 0.0
        )''')
        conn.commit()

def add_to_watchlist(chat_id: str, token: str, target_price: float, direction: str = 'ABOVE'):
    init_watchlist_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            'INSERT INTO watchlist (chat_id, token_address, target_price_usd, direction) VALUES (?,?,?,?)',
            (chat_id, token, target_price, direction)
        )
        conn.commit()

def get_active_watchlist(chat_id: str):
    init_watchlist_db()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, token_address, target_price_usd, direction FROM watchlist WHERE chat_id=? AND status='ACTIVE'",
            (chat_id,)
        ).fetchall()
    return [{'id': r[0], 'token': r[1], 'target': r[2], 'direction': r[3]} for r in rows]

def log_tx(chat_id: str, token: str, action: str, eth_amount: float, tx_hash: str, pnl_pct: float = 0.0):
    init_watchlist_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            'INSERT INTO tx_history (chat_id, token_address, action, eth_amount, tx_hash, timestamp, pnl_pct) VALUES (?,?,?,?,?,?,?)',
            (chat_id, token, action, eth_amount, tx_hash, time.time(), pnl_pct)
        )
        conn.commit()

def get_tx_history(chat_id: str, limit: int = 10):
    init_watchlist_db()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            'SELECT token_address, action, eth_amount, tx_hash, timestamp, pnl_pct FROM tx_history WHERE chat_id=? ORDER BY timestamp DESC LIMIT ?',
            (chat_id, limit)
        ).fetchall()
    return [{'token': r[0], 'action': r[1], 'eth': r[2], 'hash': r[3], 'ts': r[4], 'pnl': r[5]} for r in rows]


class WatchlistEngine:
    '''Phase 7.3: Price Alert Daemon.'''
    def __init__(self, telegram_service=None):
        self.telegram_service = telegram_service
        
    def poll(self):
        init_watchlist_db()
        while True:
            time.sleep(30)
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    rows = conn.execute(
                        "SELECT DISTINCT chat_id FROM watchlist WHERE status='ACTIVE'"
                    ).fetchall()
                for row in rows:
                    self._check_alerts(row[0])
            except Exception:
                pass
                
    def _check_alerts(self, chat_id: str):
        alerts = get_active_watchlist(chat_id)
        for alert in alerts:
            # Simulate current price
            current_price = round(random.uniform(0.000001, 0.01), 8)
            triggered = (
                (alert['direction'] == 'ABOVE' and current_price >= alert['target']) or
                (alert['direction'] == 'BELOW' and current_price <= alert['target'])
            )
            if triggered and self.telegram_service:
                self.telegram_service.send_message(
                    f"🔔 <b>Price Alert Triggered!</b>\\n\\n"
                    f"Token: <code>{alert['token']}</code>\\n"
                    f"Current: \\n"
                    f"Target: {alert['direction']} \\n\\n"
                    f"<i>Alert fired. Use /buy to enter or /watch to reset.</i>",
                    chat_id
                )
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute("UPDATE watchlist SET status='FIRED' WHERE id=?", (alert['id'],))
                    conn.commit()
