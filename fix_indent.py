import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith('        referrer_id = None'):
        start_idx = i
        break

for i in range(start_idx, len(lines)):
    if 'elif cmd_text.startswith("/takeprofit"):' in lines[i]:
        end_idx = i
        break

# The lines from start_idx to end_idx-1 are currently unindented relative to the 'if' block.
# We need to add 4 spaces to all of them.
for i in range(start_idx, end_idx):
    if lines[i].strip():
        lines[i] = '    ' + lines[i]

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
