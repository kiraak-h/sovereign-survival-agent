import sys
with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start = -1
end = -1
for i, line in enumerate(lines):
    if 'elif data == "menu_trenches":' in line:
        start = i
    if start != -1 and 'elif data == "menu_settings":' in line:
        end = i
        break

if start != -1 and end != -1:
    with open('core/menu_trenches_replacement.py', 'r', encoding='utf-8') as f:
        replacement = f.read()
    
    lines = lines[:start] + [replacement + '\n'] + lines[end:]
    
    with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Replaced successfully")
else:
    print("Could not find boundaries")
