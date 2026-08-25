import time
import sqlite3
import os
import json
import urllib.request
import ssl

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'sniper_wallets.db')
_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE

def get_real_price(token_address: str) -> float:
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5, context=_ctx) as r:
            data = json.loads(r.read())
        pairs = data.get('pairs', [])
        if pairs:
            # Sort by liquidity to get the most accurate price
            pairs.sort(key=lambda p: float(p.get('liquidity', {}).get('usd', 0) or 0), reverse=True)
            return float(pairs[0].get('priceUsd', 0))
    except Exception:
        pass
    return 0.0

def init_watchlist_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                token_address TEXT,
                target_price REAL,
                direction TEXT,
                status TEXT DEFAULT 'PENDING'
            )
        ''')

def add_watchlist_alert(chat_id: str, token_address: str, target_price: float, direction: str) -> int:
    init_watchlist_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO watchlist (chat_id, token_address, target_price, direction, status) VALUES (?, ?, ?, ?, 'PENDING')",
            (chat_id, token_address, target_price, direction.upper())
        )
        return cursor.lastrowid

def get_active_watchlist(chat_id: str = None) -> list:
    init_watchlist_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if chat_id:
            cursor.execute("SELECT * FROM watchlist WHERE status = 'PENDING' AND chat_id = ?", (chat_id,))
        else:
            cursor.execute("SELECT * FROM watchlist WHERE status = 'PENDING'")
        return [dict(row) for row in cursor.fetchall()]

def mark_alert_triggered(alert_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE watchlist SET status = 'TRIGGERED' WHERE id = ?", (alert_id,))

class WatchlistEngine:
    def __init__(self, telegram_service=None):
        self.telegram_service = telegram_service

    def poll(self):
        init_watchlist_db()
        while True:
            time.sleep(30)
            try:
                alerts = get_active_watchlist()
                for alert in alerts:
                    current_price = get_real_price(alert['token_address'])
                    if current_price == 0.0:
                        continue
                        
                    triggered = (
                        (alert['direction'] == 'ABOVE' and current_price >= alert['target_price']) or
                        (alert['direction'] == 'BELOW' and current_price <= alert['target_price'])
                    )
                    
                    if triggered:
                        mark_alert_triggered(alert['id'])
                        if self.telegram_service:
                            self.telegram_service.send_message(
                                f"🔔 <b>PRICE ALERT TRIGGERED!</b>\n\n"
                                f"Token: <code>{alert['token_address']}</code>\n"
                                f"Target: \n"
                                f"Current: \n\n"
                                f"<i>Use /sell or /buy to execute.</i>",
                                alert['chat_id']
                            )
            except Exception as e:
                print(f"Watchlist Error: {e}")
