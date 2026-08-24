import sys
import re

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r"(elif cmd_text == \"/help\":)"

new_cmd = '''elif cmd_text.startswith("/takeprofit"):
            parts = cmd_text.split()
            if len(parts) == 3:
                token = parts[1]
                try:
                    target_pct = float(parts[2].replace("%", ""))
                    from core.sniper_wallet import create_limit_order
                    create_limit_order(chat_id, token, target_pct)
                    self.send_message(f"✅ <b>Limit Order Set</b>\\nTarget: +{target_pct}%\\nToken: <code>{token}</code>\\n\\n<i>The Sovereign Limit Engine is now monitoring this asset.</i>", chat_id)
                except ValueError:
                    self.send_message("❌ Invalid percentage. Usage: /takeprofit [token] 50", chat_id)
            else:
                self.send_message("❌ Usage: /takeprofit [token] [percentage]", chat_id)
                
        \\1'''

content = re.sub(pattern, new_cmd, content)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added /takeprofit command!")
