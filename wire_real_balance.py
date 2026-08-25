import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace fake portfolio call with real portfolio engine
content = content.replace(
    'from core.dex_router import get_portfolio_positions',
    'from core.portfolio import get_portfolio_positions, get_eth_balance'
)

# Update /start to show REAL ETH balance
old_start_balance = "Balance: 0.000 ETH (.00)"
# We'll inject live balance into the start handler
old_start_msg = '''            msg = (
                f"<b>Sovereign Sniper · Base L2 🛡️</b>\\n"
                f"<code>{wallet['address']}</code> <i>(Tap to copy)</i>\\n"
                f"<b>Balance:</b> 0.000 ETH (.00)\\n"'''

new_start_msg = '''            from core.portfolio import get_eth_balance
            eth_bal = get_eth_balance(wallet['address'])
            eth_usd = round(eth_bal * 2500, 2)
            msg = (
                f"<b>Sovereign Sniper · Base L2 🛡️</b>\\n"
                f"<code>{wallet['address']}</code> <i>(Tap to copy)</i>\\n"
                f"<b>Balance:</b> {eth_bal:.4f} ETH ()\\n"'''

content = content.replace(old_start_msg, new_start_msg)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
