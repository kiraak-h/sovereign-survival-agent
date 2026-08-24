import sys

# Wire all new engines into server.py
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Imports
content = content.replace(
    'from core.anti_rug_engine import AntiRugEngine',
    'from core.anti_rug_engine import AntiRugEngine\nfrom core.dca_engine import DCAEngine\nfrom core.watchlist_engine import WatchlistEngine'
)

# Instantiate
content = content.replace(
    '_anti_rug_engine = AntiRugEngine()',
    '_anti_rug_engine = AntiRugEngine()\n_dca_engine = DCAEngine()\n_watchlist_engine = WatchlistEngine()'
)

# Pass telegram service
content = content.replace(
    '_anti_rug_engine.telegram_service = _telegram_service',
    '_anti_rug_engine.telegram_service = _telegram_service\n_dca_engine.telegram_service = _telegram_service\n_watchlist_engine.telegram_service = _telegram_service'
)

# Start threads
content = content.replace(
    'threading.Thread(target=_anti_rug_engine.poll, daemon=True).start()',
    'threading.Thread(target=_anti_rug_engine.poll, daemon=True).start()\n    threading.Thread(target=_dca_engine.poll, daemon=True).start()\n    threading.Thread(target=_watchlist_engine.poll, daemon=True).start()'
)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("server.py updated")
