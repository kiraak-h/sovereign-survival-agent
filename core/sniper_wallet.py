import os
import sqlite3
from eth_account import Account
from cryptography.fernet import Fernet
import json

# Setup encryption key for wallets
MASTER_KEY = os.environ.get("SNIPER_MASTER_KEY", Fernet.generate_key().decode())
cipher = Fernet(MASTER_KEY.encode())

def init_db():
    with sqlite3.connect("sniper_wallets.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users
                        (chat_id TEXT PRIMARY KEY, 
                         wallet_address TEXT, 
                         encrypted_private_key TEXT)''')

def get_or_create_wallet(chat_id: str) -> dict:
    init_db()
    with sqlite3.connect("sniper_wallets.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                "address": row["wallet_address"],
                "private_key": cipher.decrypt(row["encrypted_private_key"].encode()).decode()
            }
            
        # Create new wallet
        Account.enable_unaudited_hdwallet_features()
        acct = Account.create()
        enc_pk = cipher.encrypt(acct.key.hex().encode()).decode()
        
        cursor.execute("INSERT INTO users (chat_id, wallet_address, encrypted_private_key) VALUES (?, ?, ?)",
                       (chat_id, acct.address, enc_pk))
        
        return {
            "address": acct.address,
            "private_key": acct.key.hex()
        }

if __name__ == "__main__":
    init_db()
    print("Sniper Wallet DB initialized.")
