import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Route menu_snipe
content = content.replace(
    '''elif data == "menu_copy":
            self.send_message("<b>👥 Copy Trade (Vampire Mode)</b>''',
    '''elif data == "menu_snipe":
            self.send_message("<b>⚡ Mempool Sniper</b>\\n\\nReply with: <code>/snipe on [MAX_SPEND_ETH] [MIN_LIQUIDITY_ETH]</code>\\n<i>Example: /snipe on 0.05 1.0</i>\\n\\nOr disable with: <code>/snipe off</code>\\n\\n<i>🚀 Monitors the Base mempool for brand new token launches and buys in Block 0 before the chart even loads. EVM Shield is active on every snipe.</i>", chat_id)
        elif data == "menu_copy":
            self.send_message("<b>👥 Copy Trade (Vampire Mode)</b>'''
)

# Route /snipe command
content = content.replace(
    "elif cmd_text.startswith(\"/copy\"):",
    """elif cmd_text.startswith("/snipe"):
            self._handle_sniper(cmd_text, chat_id)
        elif cmd_text.startswith("/copy"):"""
)

# Add _handle_sniper method
new_method = '''
    def _handle_sniper(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) < 2:
            return self.send_message("❌ Usage: /snipe on [MAX_SPEND_ETH] [MIN_LIQUIDITY_ETH]  or  /snipe off", chat_id)
            
        action = parts[1].lower()
        
        if action == "off":
            from server import _mempool_sniper
            _mempool_sniper.disable(chat_id)
            return self.send_message("🔴 <b>Mempool Sniper Deactivated.</b>", chat_id)
            
        if action != "on" or len(parts) < 3:
            return self.send_message("❌ Usage: /snipe on [MAX_SPEND_ETH] [MIN_LIQUIDITY_ETH]", chat_id)
            
        try:
            max_spend = float(parts[2])
            min_liquidity = float(parts[3]) if len(parts) >= 4 else 1.0
        except ValueError:
            return self.send_message("❌ Invalid amount.", chat_id)
            
        from server import _mempool_sniper
        _mempool_sniper.enable(chat_id, max_spend, min_liquidity)
        
        self.send_message(
            f"🟢 <b>Mempool Sniper ACTIVATED!</b>\\n\\n"
            f"Max Spend: {max_spend} ETH per snipe\\n"
            f"Min Liquidity Filter: {min_liquidity} ETH\\n\\n"
            f"<i>Listening to Base mempool for new Uniswap pairs...\\nEVM Honeypot Shield is active on every snipe.\\nType /snipe off to deactivate.</i>",
            chat_id
        )
'''

content += new_method

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Sniper UI wired!")
