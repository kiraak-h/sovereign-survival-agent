import sqlite3
import secrets
from pathlib import Path

class PrepaidLedger:
    def __init__(self, db_path='treasury_ledger.db'):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    api_key TEXT PRIMARY KEY,
                    client_name TEXT,
                    balance_usdc REAL,
                    total_audits INTEGER DEFAULT 0
                )
            ''')
            
    def generate_key(self, client_name: str, initial_deposit_usdc: float) -> str:
        api_key = f"sov_live_{secrets.token_hex(16)}"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('INSERT INTO api_keys (api_key, client_name, balance_usdc) VALUES (?, ?, ?)',
                         (api_key, client_name, initial_deposit_usdc))
        return api_key
        
    def charge_audit(self, api_key: str, fee_usdc: float) -> tuple[bool, str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT balance_usdc FROM api_keys WHERE api_key = ?', (api_key,))
            row = cursor.fetchone()
            if not row:
                return False, "Invalid API Key. Purchase a key at sovereign-agent.com"
            balance = row[0]
            if balance < fee_usdc:
                return False, f"Insufficient prepaid balance. Current balance: $ USDC. Please top up."
                
            cursor.execute('''
                UPDATE api_keys 
                SET balance_usdc = balance_usdc - ?, total_audits = total_audits + 1 
                WHERE api_key = ?
            ''', (fee_usdc, api_key))
            return True, "Payment successful"

    def get_balance(self, api_key: str) -> float:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT balance_usdc FROM api_keys WHERE api_key = ?', (api_key,))
            row = cursor.fetchone()
            return row[0] if row else 0.0
