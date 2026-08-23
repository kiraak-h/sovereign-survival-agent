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

def init_db():
    with sqlite3.connect("sniper_wallets.db") as conn:
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

def get_or_create_wallet(chat_id: str, referrer_id: Optional[str] = None) -> dict:
    init_db()
    with sqlite3.connect("sniper_wallets.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        
        if row:
            # Already exists, just return it
            return {
                "address": row["wallet_address"],
                "private_key": cipher.decrypt(row["encrypted_private_key"].encode()).decode()
            }
            
        Account.enable_unaudited_hdwallet_features()
        acct = Account.create()
        enc_pk = cipher.encrypt(acct.key.hex().encode()).decode()
        
        cursor.execute("INSERT INTO users (chat_id, wallet_address, encrypted_private_key, referrer_id, referral_rewards_eth) VALUES (?, ?, ?, ?, 0.0)",
                       (chat_id, acct.address, enc_pk, referrer_id))
        
        return {
            "address": acct.address,
            "private_key": acct.key.hex()
        }

def get_wallet_by_chat_id(chat_id: str) -> Optional[dict]:
    with sqlite3.connect("sniper_wallets.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        if row:
            return {
                "address": row["wallet_address"],
                "referrer_id": row["referrer_id"],
                "rewards": row["referral_rewards_eth"]
            }
    return None

def add_referral_reward(chat_id: str, amount_eth: float):
    with sqlite3.connect("sniper_wallets.db") as conn:
        conn.execute("UPDATE users SET referral_rewards_eth = referral_rewards_eth + ? WHERE chat_id = ?", (amount_eth, chat_id))

def get_referral_stats(chat_id: str) -> dict:
    with sqlite3.connect("sniper_wallets.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (chat_id,))
        count = cursor.fetchone()[0]
        cursor.execute("SELECT referral_rewards_eth FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        rewards = row[0] if row else 0.0
        return {"count": count, "rewards": rewards}
