import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Route menu_buy and menu_sell properly
content = content.replace(
    '        elif data.startswith("menu_"):',
    '''        elif data == "menu_buy":
            self.send_message("<b>🟢 Buy Token</b>\\n\\nReply with: <code>/buy [TOKEN_ADDRESS] [ETH_AMOUNT]</code>\\n<i>Example: /buy 0x123... 0.5</i>\\n\\n<i>🛡️ Every buy is automatically protected by the EVM Honeypot Simulator.</i>", chat_id)
        elif data == "menu_sell":
            self.handle_command("/positions", chat_id)
        elif data.startswith("menu_"):'''
)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
