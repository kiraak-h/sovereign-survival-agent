import os
import sys

filepath = 'core/sniper_wallet.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add to init_db
init_db_patch = '''
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
            
        conn.execute(\'''
            CREATE TABLE IF NOT EXISTS copy_targets (
                id SERIAL PRIMARY KEY,
                chat_id TEXT,
                target_address TEXT,
                max_spend_eth REAL,
                is_active INTEGER DEFAULT 1
            )
        \''')
'''
content = content.replace('''
        # Migration: Add referrer tracking
        try:
            conn.execute('ALTER TABLE users ADD COLUMN referrer_id TEXT')
            conn.execute('ALTER TABLE users ADD COLUMN referral_rewards_eth REAL DEFAULT 0.0')
        except Exception:
            pass # Columns already exist''', init_db_patch)

# Add new functions at the end
new_funcs = '''
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
'''
content += new_funcs

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated core/sniper_wallet.py")
