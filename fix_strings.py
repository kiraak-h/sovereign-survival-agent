import os

filepath = 'core/telegram_bot_service.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix literal newlines in single-line strings
content = content.replace('caption = f"✅ <b>Sell Executed!</b>\\n\\nDumped', 'caption = f"✅ <b>Sell Executed!</b>\\\\n\\\\nDumped')
content = content.replace('msg = "🦇 <b>Your Vampire Targets:</b>\\n\\n"', 'msg = "🦇 <b>Your Vampire Targets:</b>\\\\n\\\\n"')
content = content.replace('msg += f"{idx+1}. <code>{addr}</code>\\n   Spend: {t[\'max_spend_eth\']} ETH | {status}\\n\\n"', 'msg += f"{idx+1}. <code>{addr}</code>\\\\n   Spend: {t[\'max_spend_eth\']} ETH | {status}\\\\n\\\\n"')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
