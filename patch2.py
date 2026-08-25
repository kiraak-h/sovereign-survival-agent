import sys
with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start = -1
end = -1
for i, line in enumerate(lines):
    if 'elif data.startswith("tsnipe_"):' in line:
        start = i
    if start != -1 and 'elif data.startswith("menu_"):' in line:
        end = i
        break

if start != -1 and end != -1:
    with open('core/tsnipe_replacement.py', 'r', encoding='utf-8') as f:
        replacement = f.read()
    
    lines = lines[:start] + [replacement + '\n'] + lines[end:]
    
    with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Replaced tsnipe successfully")
else:
    print("Could not find boundaries")
