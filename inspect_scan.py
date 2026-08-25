import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The duplicate /scan: exact match at line ~8 position catches /scan with no args
# and sends to old handler. The startswith version further down is the NEW real one.
# Fix: make the exact match also call the real handler
content = content.replace(
    '        elif cmd_text == "/scan":\n            self._handle_vitals(chat_id)',
    '        elif cmd_text == "/scan":\n            self._handle_scan("/scan", chat_id)'
)

# Actually let's search more carefully and see what the exact /scan == block does
with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '/scan' in line:
        print(str(i+1) + ': ' + line.rstrip())
