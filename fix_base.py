import sys
with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix SOL reference
content = content.replace('Add SOL or reduce your tx amount', 'Add ETH or reduce your tx amount')
# Fix Solscan reference
content = content.replace('Solscan.io', 'Basescan.org')

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Scrubbed Solana references!")
