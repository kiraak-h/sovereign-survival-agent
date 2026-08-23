import sqlite3
import secrets
from pathlib import Path

class PrepaidLedger:
    def __init__(self, db_path='treasury_ledger.db'):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    api_key TEXT PRIMARY KEY,
                    client_name TEXT,
                    balance_usdc REAL,
                    total_audits INTEGER DEFAULT 0,
                    tx_hash TEXT UNIQUE NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS unclaimed_permits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payer_address TEXT NOT NULL,
                    token_address TEXT NOT NULL,
                    amount_usdc REAL NOT NULL,
                    nonce INTEGER NOT NULL,
                    deadline INTEGER NOT NULL,
                    signature TEXT NOT NULL,
                    status TEXT DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def save_permit(self, permit_data: dict) -> bool:
        """Saves a verified EIP-2612 permit to the database so the sweeper daemon can cash it later."""
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("""
                    INSERT INTO unclaimed_permits 
                    (payer_address, token_address, amount_usdc, nonce, deadline, signature) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    permit_data.get("payer_address"),
                    permit_data.get("token_address"),
                    permit_data.get("amount_usdc"),
                    permit_data.get("nonce"),
                    permit_data.get("deadline"),
                    permit_data.get("signature")
                ))
                return True
            except sqlite3.IntegrityError:
                return False
            
    def generate_key(self, client_name: str, initial_deposit_usdc: float, tx_hash: str) -> str:
        api_key = f"sov_live_{secrets.token_hex(16)}"
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('INSERT INTO api_keys (api_key, client_name, balance_usdc, tx_hash) VALUES (?, ?, ?, ?)',
                             (api_key, client_name, initial_deposit_usdc, tx_hash))
            except sqlite3.IntegrityError:
                raise ValueError("Transaction hash already used or invalid.")
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
