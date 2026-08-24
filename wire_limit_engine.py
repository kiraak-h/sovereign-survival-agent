import sys

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Import
if 'from core.limit_engine import LimitEngine' not in content:
    content = content.replace(
        'from core.telegram_bot_service import TelegramBotService',
        'from core.telegram_bot_service import TelegramBotService\nimport threading\nfrom core.limit_engine import LimitEngine'
    )

# 2. Instantiate LimitEngine
if '_limit_engine = LimitEngine()' not in content:
    content = content.replace(
        '_telegram_service = TelegramBotService(',
        '_limit_engine = LimitEngine()\n_telegram_service = TelegramBotService('
    )

# 3. Start LimitEngine inside on_startup
if '_limit_engine.poll' not in content:
    content = content.replace(
        '    _telegram_service.start()',
        '    _telegram_service.start()\n    threading.Thread(target=_limit_engine.poll, daemon=True).start()'
    )

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
