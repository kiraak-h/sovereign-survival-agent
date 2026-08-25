import sys
with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the token name to be a Dexscreener link
target1 = '''msg_text += f"{safe_icon} <b>{t['name']}</b>\\n"'''
replacement1 = '''msg_text += f"{safe_icon} <b><a href='https://dexscreener.com/base/{t['address']}'>{t['name']}</a></b>\\n"'''

# 2. Update the button text
target2 = '''inline_kb.append([{"text": f"🔫 1-Click Snipe 0.05 ETH", "callback_data": cb_data[:64]}])'''
replacement2 = '''inline_kb.append([{"text": f"🔫 1-Click Snipe 0.02 ETH", "callback_data": cb_data[:64]}])'''

# 3. Update the send_message amount
target3 = '''self.send_message(f"⚡ <b>1-CLICK SNIPE INITIATED</b>\\n\\nToken: <code>{token_addr}</code>\\nAmount: 0.05 ETH\\n\\n<i>Executing via Private MEV Router...</i>", chat_id)'''
replacement3 = '''self.send_message(f"⚡ <b>1-CLICK SNIPE INITIATED</b>\\n\\nToken: <code>{token_addr}</code>\\nAmount: 0.02 ETH\\n\\n<i>Executing via Private MEV Router...</i>", chat_id)'''

# 4. Update execute_snipe amount
target4 = '''result = execute_snipe(wallet['private_key'], token_addr, 0.05)'''
replacement4 = '''result = execute_snipe(wallet['private_key'], token_addr, 0.02)'''

if target1 in content: content = content.replace(target1, replacement1)
else: print("Target 1 not found")

if target2 in content: content = content.replace(target2, replacement2)
else: print("Target 2 not found")

if target3 in content: content = content.replace(target3, replacement3)
else: print("Target 3 not found")

if target4 in content: content = content.replace(target4, replacement4)
else: print("Target 4 not found")

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch applied")
