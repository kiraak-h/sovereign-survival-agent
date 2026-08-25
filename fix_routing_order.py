import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# There are TWO /scan entries still — exact match AND startswith
# The exact match (cmd_text == "/scan") points to old handler, remove it
# The startswith version ("/scan") is the correct one
content = content.replace(
    '        elif cmd_text == "/scan":\n            self._handle_scan(cmd_text, chat_id)\n        elif cmd_text == "/status":',
    '        elif cmd_text == "/status":'
)

# Also /watch == before /watchlist — watchlist must come first
content = content.replace(
    '        elif cmd_text.startswith("/watch"):\n            self._handle_watch(cmd_text, chat_id)\n        elif cmd_text == "/watchlist":\n            self._handle_watchlist(chat_id)',
    '        elif cmd_text == "/watchlist":\n            self._handle_watchlist(chat_id)\n        elif cmd_text.startswith("/watch"):\n            self._handle_watch(cmd_text, chat_id)'
)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed routing order!")
