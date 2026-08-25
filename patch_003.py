import sys
with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''msg_text += f"💧 Liq:  | 📈 MCAP:  | 5m: {chg_icon}{t['chg']:.1f}%\\n\\n"'''
replacement = '''msg_text += f"💧 Liq: ${t['liq']:,.0f} | 📈 MCAP: ${t['fdv']:,.0f} | 5m: {chg_icon}{t['chg']:.1f}%\\n\\n"'''

if target in content:
    content = content.replace(target, replacement)
    with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed formatting")
else:
    print("Target not found")
