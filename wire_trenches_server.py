import sys

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'from core.watchlist_engine import WatchlistEngine',
    'from core.watchlist_engine import WatchlistEngine\nfrom core.trenches_engine import TrenchesEngine'
)

content = content.replace(
    '_watchlist_engine = WatchlistEngine()',
    '_watchlist_engine = WatchlistEngine()\n_trenches_engine = TrenchesEngine()'
)

content = content.replace(
    '_watchlist_engine.telegram_service = _telegram_service',
    '_watchlist_engine.telegram_service = _telegram_service\n_trenches_engine.telegram_service = _telegram_service'
)

content = content.replace(
    'threading.Thread(target=_watchlist_engine.poll, daemon=True).start()',
    'threading.Thread(target=_watchlist_engine.poll, daemon=True).start()\n    threading.Thread(target=_trenches_engine.poll, daemon=True).start()'
)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("server.py updated")
