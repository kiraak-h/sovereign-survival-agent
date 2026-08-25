import time
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'sniper_wallets.db')

def init_dca_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS dca_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            token_address TEXT NOT NULL,
            eth_amount REAL NOT NULL,
            interval_minutes INTEGER NOT NULL,
            next_execution_ts REAL NOT NULL,
            status TEXT DEFAULT 'ACTIVE'
        )''')
        conn.commit()

def create_dca_order(chat_id: str, token: str, eth_amount: float, interval_minutes: int):
    init_dca_db()
    next_ts = time.time() + (interval_minutes * 60)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            'INSERT INTO dca_orders (chat_id, token_address, eth_amount, interval_minutes, next_execution_ts) VALUES (?,?,?,?,?)',
            (chat_id, token, eth_amount, interval_minutes, next_ts)
        )
        conn.commit()

def get_due_dca_orders():
    init_dca_db()
    now = time.time()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, chat_id, token_address, eth_amount, interval_minutes FROM dca_orders WHERE status='ACTIVE' AND next_execution_ts <= ?",
            (now,)
        ).fetchall()
    return [{'id': r[0], 'chat_id': r[1], 'token': r[2], 'eth_amount': r[3], 'interval_minutes': r[4]} for r in rows]

def reschedule_dca_order(order_id: int, interval_minutes: int):
    next_ts = time.time() + (interval_minutes * 60)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('UPDATE dca_orders SET next_execution_ts=? WHERE id=?', (next_ts, order_id))
        conn.commit()

def cancel_dca_order(chat_id: str, token: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE dca_orders SET status='CANCELLED' WHERE chat_id=? AND token_address=? AND status='ACTIVE'", (chat_id, token))
        conn.commit()


class DCAEngine:
    def __init__(self, telegram_service=None):
        self.telegram_service = telegram_service
        
    def poll(self):
        init_dca_db()
        while True:
            time.sleep(60)
            try:
                orders = get_due_dca_orders()
                for order in orders:
                    self._execute_dca(order)
            except Exception:
                pass
                
    def _execute_dca(self, order: dict):
        try:
            from core.sniper_wallet import get_or_create_wallet
            from core.token_scanner import check_honeypot
            from core.dex_router import execute_snipe
            
            wallet = get_or_create_wallet(order['chat_id'])
            if not wallet:
                return
            
            if not check_honeypot(order['token']):
                if self.telegram_service:
                    self.telegram_service.send_message(
                        f"🚨 <b>DCA Buy Skipped - Honeypot Detected!</b>\n"
                        f"Token: <code>{order['token']}</code>\n"
                        f"<i>Rescheduling next attempt in {order['interval_minutes']} minutes.</i>",
                        order['chat_id']
                    )
            else:
                trade_result = execute_snipe(wallet['private_key'], order['token'], order['eth_amount'])
                if self.telegram_service and trade_result['status'] == 'SUCCESS':
                    self.telegram_service.send_message(
                        f"✅ <b>DCA Buy Executed!</b>\n\n"
                        f"Token: <code>{order['token']}</code>\n"
                        f"Amount: {trade_result['trade_eth']} ETH\n"
                        f"Next buy in: {order['interval_minutes']} minutes\n"
                        f"Tx: <code>{trade_result.get('tx_hash', trade_result.get('simulated_tx_hash'))}</code>",
                        order['chat_id']
                    )
                    
            reschedule_dca_order(order['id'], order['interval_minutes'])
        except Exception as e:
            if self.telegram_service:
                self.telegram_service.send_message(f"❌ DCA Error: {e}", order['chat_id'])
