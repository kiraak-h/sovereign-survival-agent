import sys

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Import and instantiate CopyEngine
content = content.replace(
    'from core.limit_engine import LimitEngine',
    'from core.limit_engine import LimitEngine\\nfrom core.copy_engine import CopyEngine'
)

content = content.replace(
    '_limit_engine = LimitEngine()',
    '_limit_engine = LimitEngine()\\n_copy_engine = CopyEngine()'
)

# Pass telegram_service to copy_engine AFTER telegram is instantiated
content = content.replace(
    '_telegram_service = TelegramBotService(',
    '_telegram_service = TelegramBotService('
)
# We will just manually inject _copy_engine.telegram_service = _telegram_service right after creation
content = content.replace(
    'static_analyzer=_static_analyzer,\\n)',
    'static_analyzer=_static_analyzer,\\n)\\n_copy_engine.telegram_service = _telegram_service'
)

# Start polling thread
content = content.replace(
    'threading.Thread(target=_limit_engine.poll, daemon=True).start()',
    'threading.Thread(target=_limit_engine.poll, daemon=True).start()\\n    threading.Thread(target=_copy_engine.poll, daemon=True).start()'
)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
