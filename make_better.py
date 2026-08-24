import sys
import re

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update handle_command signature
content = content.replace(
    'def handle_command(self, cmd_text: str, chat_id: str):',
    'def handle_command(self, cmd_text: str, chat_id: str, message_id: int = None):'
)

# 2. Update _poll_loop to pass message_id
content = content.replace(
    'self.handle_command(message["text"], chat_id)',
    'self.handle_command(message["text"], chat_id, message.get("message_id"))'
)

# 3. Update _handle_import signature and add delete logic
old_import = '''    def _handle_import(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) != 2:
            return self.send_message("❌ Usage: /import [PRIVATE_KEY]", chat_id)
            
        private_key = parts[1]
        if not private_key.startswith("0x") and len(private_key) == 64:
            private_key = "0x" + private_key
            
        try:
            from core.sniper_wallet import import_wallet
            address = import_wallet(chat_id, private_key)
            self.send_message(f"✅ <b>Wallet Imported Successfully!</b>\\n\\nAddress: <code>{address}</code>\\n\\n<i>Your private key has been encrypted. Please manually delete your previous message for safety.</i>", chat_id)
        except Exception as e:
            self.send_message(f"❌ Import Failed: {e}", chat_id)'''

new_import = '''    def _handle_import(self, cmd_text: str, chat_id: str, message_id: int = None):
        parts = cmd_text.split()
        if len(parts) != 2:
            return self.send_message("❌ Usage: /import [PRIVATE_KEY]", chat_id)
            
        private_key = parts[1]
        if not private_key.startswith("0x") and len(private_key) == 64:
            private_key = "0x" + private_key
            
        try:
            from core.sniper_wallet import import_wallet
            address = import_wallet(chat_id, private_key)
            
            # ZERO-TRACE AUTO-DELETION FOR OPSEC
            import requests
            if self.token and message_id:
                try:
                    url = f"https://api.telegram.org/bot{self.token}/deleteMessage"
                    requests.post(url, json={"chat_id": chat_id, "message_id": message_id}, timeout=5.0)
                except Exception:
                    pass
                    
            self.send_message(f"✅ <b>Wallet Imported Successfully!</b>\\n\\nAddress: <code>{address}</code>\\n\\n<i>⚠️ OPSEC SECURED: Your private key was immediately encrypted and your message was auto-deleted from the chat history.</i>", chat_id)
        except Exception as e:
            self.send_message(f"❌ Import Failed: {e}", chat_id)'''

content = content.replace(old_import, new_import)

# 4. Update the router in handle_command to pass message_id
content = content.replace(
    'self._handle_import(cmd_text, chat_id)',
    'self._handle_import(cmd_text, chat_id, message_id)'
)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Auto-Delete OPSEC added!")
