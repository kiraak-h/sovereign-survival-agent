import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Route menu_snipe button to include anti-rug info, and add anti-rug to settings area
content = content.replace(
    '''elif data == "menu_snipe":
            self.send_message(''',
    '''elif data == "menu_scanner":
            self.send_message("<b>🔍 Token Scanner</b>\\n\\nReply with: <code>/scan [TOKEN_ADDRESS]</code>\\n<i>Runs a full EVM simulation + honeypot + tax analysis on any token before you commit capital.</i>", chat_id)
        elif data == "menu_snipe":
            self.send_message('''
)

# Wire /antrug command
content = content.replace(
    'elif cmd_text.startswith("/snipe"):',
    '''elif cmd_text.startswith("/antrug"):
            self._handle_antrug(cmd_text, chat_id)
        elif cmd_text.startswith("/snipe"):'''
)

# Wire settings to show antrug status
content = content.replace(
    '''elif data == "menu_settings":
            self.send_message(f"<i>Feature 'Settings' coming soon in Phase 6...</i>", chat_id)''',
    '''elif data == "menu_settings":
            self.send_message(
                "<b>⚙️ Settings</b>\\n\\n"
                "🛡️ <b>Anti-Rugpull Shield:</b>\\n  <code>/antrug on</code> — Enable protection\\n  <code>/antrug off</code> — Disable protection\\n\\n"
                "⚡ <b>Mempool Sniper:</b>\\n  <code>/snipe on [ETH] [MIN_LIQ]</code>\\n  <code>/snipe off</code>\\n\\n"
                "👥 <b>Copy Trade:</b>\\n  <code>/copy [ADDRESS] [MAX_ETH]</code>\\n\\n"
                "🎯 <b>Take Profit:</b>\\n  <code>/takeprofit [TOKEN] [PCT]</code>",
                chat_id
            )'''
)

# Add _handle_antrug method
new_method = '''
    def _handle_antrug(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) < 2:
            return self.send_message("❌ Usage: /antrug on  or  /antrug off", chat_id)
            
        action = parts[1].lower()
        from server import _anti_rug_engine
        
        if action == "on":
            _anti_rug_engine.enable(chat_id)
            self.send_message(
                "🛡️ <b>Anti-Rugpull Shield ACTIVATED!</b>\\n\\n"
                "Monitoring the Base mempool for:\\n"
                "• removeLiquidity() calls\\n"
                "• Malicious setTax() spikes\\n"
                "• Ownership transfers to dead addresses\\n\\n"
                "<i>If a rugpull is detected, I will execute a 5x-priority emergency sell to exit before the rug is confirmed.</i>",
                chat_id
            )
        elif action == "off":
            _anti_rug_engine.disable(chat_id)
            self.send_message("🔴 <b>Anti-Rugpull Shield Deactivated.</b>", chat_id)
        else:
            self.send_message("❌ Usage: /antrug on  or  /antrug off", chat_id)
'''

content += new_method

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Anti-Rug UI wired!")
