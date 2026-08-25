import os
import sqlite3
from eth_account import Account
from cryptography.fernet import Fernet
from typing import Optional

MASTER_KEY = os.environ.get("SNIPER_MASTER_KEY")
if not MASTER_KEY:
    key_file = "sniper_master.key"
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            MASTER_KEY = f.read().strip()
    else:
        MASTER_KEY = Fernet.generate_key().decode()
        with open(key_file, "w") as f:
            f.write(MASTER_KEY)

cipher = Fernet(MASTER_KEY.encode())
DB_PATH = "sniper_wallets.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users
                        (chat_id TEXT PRIMARY KEY, 
                         wallet_address TEXT, 
                         encrypted_private_key TEXT)''')
        # Migration: Add referrer tracking
        try:
            conn.execute('ALTER TABLE users ADD COLUMN referrer_id TEXT')
            conn.execute('ALTER TABLE users ADD COLUMN referral_rewards_eth REAL DEFAULT 0.0')
        except sqlite3.OperationalError:
            pass # Columns already exist
            
        conn.execute('''
            CREATE TABLE IF NOT EXISTS limit_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                token_address TEXT,
                target_percentage REAL,
                entry_price REAL DEFAULT 0.0,
                status TEXT DEFAULT 'PENDING'
            )
        ''')

def get_or_create_wallet(chat_id: str, referrer_id: Optional[str] = None) -> dict:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                "address": row["wallet_address"],
                "private_key": cipher.decrypt(row["encrypted_private_key"].encode()).decode(),
                "referrer_id": row["referrer_id"],
                "rewards": row["referral_rewards_eth"]
            }
            
        Account.enable_unaudited_hdwallet_features()
        acct = Account.create()
        enc_pk = cipher.encrypt(acct.key.hex().encode()).decode()
        
        cursor.execute("INSERT INTO users (chat_id, wallet_address, encrypted_private_key, referrer_id, referral_rewards_eth) VALUES (?, ?, ?, ?, 0.0)",
                       (chat_id, acct.address, enc_pk, referrer_id))
        
        return {
            "address": acct.address,
            "private_key": acct.key.hex(),
            "referrer_id": referrer_id,
            "rewards": 0.0
        }

def get_wallet_by_chat_id(chat_id: str) -> Optional[dict]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        if row:
            return {
                "address": row["wallet_address"],
                "private_key": cipher.decrypt(row["encrypted_private_key"].encode()).decode(),
                "referrer_id": row["referrer_id"],
                "rewards": row["referral_rewards_eth"]
            }
    return None

def import_wallet(chat_id: str, private_key: str) -> str:
    Account.enable_unaudited_hdwallet_features()
    # Strip 0x if present for uniformity in encryption
    if private_key.startswith("0x"):
        private_key = private_key[2:]
        
    account = Account.from_key(private_key)
    address = account.address
    enc_pk = cipher.encrypt(private_key.encode()).decode()
    
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id FROM users WHERE chat_id = ?", (chat_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("UPDATE users SET wallet_address = ?, encrypted_private_key = ? WHERE chat_id = ?", (address, enc_pk, chat_id))
        else:
            cursor.execute("INSERT INTO users (chat_id, wallet_address, encrypted_private_key, referrer_id, referral_rewards_eth) VALUES (?, ?, ?, ?, 0.0)", (chat_id, address, enc_pk, None))
            
    return address

def add_referral_reward(chat_id: str, amount_eth: float):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE users SET referral_rewards_eth = referral_rewards_eth + ? WHERE chat_id = ?", (amount_eth, chat_id))

def get_referral_stats(chat_id: str) -> dict:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (chat_id,))
        count = cursor.fetchone()[0]
        cursor.execute("SELECT referral_rewards_eth FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        rewards = row[0] if row else 0.0
        return {"count": count, "rewards": rewards}

def create_limit_order(chat_id: str, token_address: str, target_percentage: float) -> int:
    init_db()
    from core.watchlist_engine import get_real_price
    entry_price = get_real_price(token_address)
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO limit_orders (chat_id, token_address, target_percentage, entry_price, status) VALUES (?, ?, ?, ?, 'PENDING')",
            (chat_id, token_address, target_percentage, entry_price)
        )
        return cursor.lastrowid

def get_pending_orders() -> list:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM limit_orders WHERE status = 'PENDING'")
        return [dict(row) for row in cursor.fetchall()]

def mark_order_executed(order_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE limit_orders SET status = 'EXECUTED' WHERE id = ?", (order_id,))
