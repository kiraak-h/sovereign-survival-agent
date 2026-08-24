import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Route menu_copy
content = content.replace(
    '''elif data.startswith("menu_"):
            self.send_message(f"<i>Feature '{data.replace('menu_', '').title()}' coming soon in Phase 6...</i>", chat_id)''',
    '''elif data == "menu_copy":
            self.send_message("<b>👥 Copy Trade (Vampire Mode)</b>\\n\\nReply with: <code>/copy [TARGET_ADDRESS] [MAX_SPEND_ETH]</code>\\n<i>Example: /copy 0x123... 0.1</i>\\n\\n<i>🦇 The bot will monitor this wallet in the mempool and front-run their buys so you get in cheaper!</i>", chat_id)
        elif data.startswith("menu_"):
            self.send_message(f"<i>Feature '{data.replace('menu_', '').title()}' coming soon in Phase 6...</i>", chat_id)'''
)

# Route /copy command
content = content.replace(
    '''elif cmd_text.startswith("/withdraw"):
            self._handle_withdraw(cmd_text, chat_id)''',
    '''elif cmd_text.startswith("/withdraw"):
            self._handle_withdraw(cmd_text, chat_id)
        elif cmd_text.startswith("/copy"):
            self._handle_copy(cmd_text, chat_id)'''
)

# Add _handle_copy
new_method = '''
    def _handle_copy(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) != 3:
            return self.send_message("❌ Usage: /copy [TARGET_ADDRESS] [MAX_SPEND_ETH]", chat_id)
            
        target = parts[1]
        try:
            max_spend = float(parts[2])
        except ValueError:
            return self.send_message("❌ Invalid ETH amount.", chat_id)
            
        from server import _copy_engine
        _copy_engine.set_target(chat_id, target, max_spend)
        
        self.send_message(f"✅ <b>Vampire Copy Trading Activated!</b>\\n\\nTarget: <code>{target}</code>\\nMax Spend: {max_spend} ETH per trade\\n\\n<i>Monitoring mempool for target transactions...</i>", chat_id)
'''

content += new_method

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
