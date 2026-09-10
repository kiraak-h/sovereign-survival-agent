import sys

filepath = 'core/sniper_wallet.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_funcs = '''
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
'''
content += new_funcs

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
