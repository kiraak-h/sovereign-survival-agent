import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Wire menu_trenches
content = content.replace(
    'elif data == "menu_settings":',
    '''elif data == "menu_trenches":
            self.send_message(
                "🕳️ <b>Trenches Mode (Ultra-Degen)</b>\\n\\n"
                "Auto-snipes micro-cap launches under your set market cap limit.\\n\\n"
                "<code>/trenches on [MAX_ETH] [MAX_MCAP]</code>\\n"
                "<i>Example: /trenches on 0.02 50000</i>\\n\\n"
                "<code>/trenches off</code> to deactivate\\n\\n"
                "⚠️ <b>WARNING:</b> High risk. EVM Shield is always active.",
                chat_id
            )
        elif data == "menu_settings":'''
)

# Wire /trenches command
content = content.replace(
    'elif cmd_text == "/history":',
    '''elif cmd_text.startswith("/trenches"):
            self._handle_trenches(cmd_text, chat_id)
        elif cmd_text == "/history":'''
)

# Wire quickbuy and quickwatch callbacks
content = content.replace(
    'elif data.startswith("sell_"):',
    '''elif data.startswith("quickbuy_"):
            token = data.replace("quickbuy_", "")
            self.send_message(f"<code>/buy {token} 0.05</code>\\n<i>Copy and send the above to execute a buy.</i>", chat_id)
        elif data.startswith("quickwatch_"):
            token = data.replace("quickwatch_", "")
            self.send_message(f"<code>/watch {token} 0.001</code>\\n<i>Edit the price and send to set a watchlist alert.</i>", chat_id)
        elif data.startswith("sell_"):'''
)

# Add trenches method
trenches_method = '''
    def _handle_trenches(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) < 2:
            return self.send_message("❌ Usage: /trenches on [MAX_ETH] [MAX_MCAP]  or  /trenches off", chat_id)
        action = parts[1].lower()
        from server import _trenches_engine
        if action == "off":
            _trenches_engine.disable(chat_id)
            return self.send_message("🔴 <b>Trenches Mode Deactivated.</b>", chat_id)
        if action != "on" or len(parts) < 3:
            return self.send_message("❌ Usage: /trenches on [MAX_ETH] [MAX_MCAP]", chat_id)
        try:
            max_eth = float(parts[2])
            max_mcap = float(parts[3]) if len(parts) >= 4 else 50000
        except ValueError:
            return self.send_message("❌ Invalid value.", chat_id)
        _trenches_engine.enable(chat_id, max_eth, max_mcap)
        self.send_message(
            f"🕳️ <b>TRENCHES MODE ACTIVATED!</b>\\n\\n"
            f"Max Spend: {max_eth} ETH per snipe\\n"
            f"Market Cap Limit: \\n"
            f"EVM Shield: Always Active\\n\\n"
            f"<i>Hunting micro-caps... I will notify you on every snipe.\\nType /trenches off to exit.</i>",
            chat_id
        )
'''
content += trenches_method

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Trenches UI wired")
