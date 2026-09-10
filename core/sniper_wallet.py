import os
from core.db import get_db
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
    with get_db(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users
                        (chat_id TEXT PRIMARY KEY, 
                         wallet_address TEXT, 
                         encrypted_private_key TEXT)''')
        # Migration: Add referrer tracking
        try:
            conn.execute('ALTER TABLE users ADD COLUMN referrer_id TEXT')
            conn.execute('ALTER TABLE users ADD COLUMN referral_rewards_eth REAL DEFAULT 0.0')
        except Exception:
            pass # Columns already exist
            
        try:
            conn.execute('ALTER TABLE users ADD COLUMN mev_tip_eth REAL DEFAULT 0.0')
        except Exception:
            pass # Column already exists
            
        conn.execute('''
            CREATE TABLE IF NOT EXISTS copy_targets (
                id SERIAL PRIMARY KEY,
                chat_id TEXT,
                target_address TEXT,
                max_spend_eth REAL,
                is_active INTEGER DEFAULT 1
            )
        ''')

            
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
    with get_db(DB_PATH) as conn:
        
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
    with get_db(DB_PATH) as conn:
        
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
    with get_db(DB_PATH) as conn:
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
    with get_db(DB_PATH) as conn:
        conn.execute("UPDATE users SET referral_rewards_eth = referral_rewards_eth + ? WHERE chat_id = ?", (amount_eth, chat_id))

def get_referral_stats(chat_id: str) -> dict:
    init_db()
    with get_db(DB_PATH) as conn:
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
    
    with get_db(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO limit_orders (chat_id, token_address, target_percentage, entry_price, status) VALUES (?, ?, ?, ?, 'PENDING')",
            (chat_id, token_address, target_percentage, entry_price)
        )
        return cursor.lastrowid

def get_pending_orders() -> list:
    init_db()
    with get_db(DB_PATH) as conn:
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM limit_orders WHERE status = 'PENDING'")
        return [dict(row) for row in cursor.fetchall()]

def mark_order_executed(order_id: int):
    with get_db(DB_PATH) as conn:
        conn.execute("UPDATE limit_orders SET status = 'EXECUTED' WHERE id = ?", (order_id,))

def set_mev_tip(chat_id: str, tip_amount: float):
    init_db()
    with get_db(DB_PATH) as conn:
        conn.execute("UPDATE users SET mev_tip_eth = ? WHERE chat_id = ?", (tip_amount, chat_id))

def get_mev_tip(chat_id: str) -> float:
    init_db()
    with get_db(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT mev_tip_eth FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        return float(row['mev_tip_eth']) if row and row['mev_tip_eth'] else 0.0

def add_copy_target(chat_id: str, target: str, max_spend: float):
    init_db()
    with get_db(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO copy_targets (chat_id, target_address, max_spend_eth, is_active) VALUES (?, ?, ?, 1)",
            (chat_id, target.lower(), max_spend)
        )

def remove_copy_target(chat_id: str, target: str):
    init_db()
    with get_db(DB_PATH) as conn:
        conn.execute("DELETE FROM copy_targets WHERE chat_id = ? AND target_address = ?", (chat_id, target.lower()))

def toggle_copy_target(chat_id: str, target: str, is_active: int):
    init_db()
    with get_db(DB_PATH) as conn:
        conn.execute("UPDATE copy_targets SET is_active = ? WHERE chat_id = ? AND target_address = ?", (is_active, chat_id, target.lower()))

def get_copy_targets(chat_id: str) -> list:
    init_db()
    with get_db(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM copy_targets WHERE chat_id = ?", (chat_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_all_active_copy_targets() -> list:
    init_db()
    with get_db(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM copy_targets WHERE is_active = 1")
        return [dict(row) for row in cursor.fetchall()]

def get_entry_price(chat_id: str, token_address: str) -> float:
    init_db()
    from core.db import get_db
    with get_db("sniper_wallets.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT entry_price FROM limit_orders WHERE chat_id = ? AND token_address = ? ORDER BY id DESC LIMIT 1",
            (chat_id, token_address.lower())
        )
        row = cursor.fetchone()
        return float(row['entry_price']) if row and row['entry_price'] else 0.0
