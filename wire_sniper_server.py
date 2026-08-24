import sys

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Import MempoolSniper
content = content.replace(
    'from core.copy_engine import CopyEngine',
    'from core.copy_engine import CopyEngine\nfrom core.mempool_sniper import MempoolSniper'
)

# Instantiate
content = content.replace(
    '_copy_engine = CopyEngine()',
    '_copy_engine = CopyEngine()\n_mempool_sniper = MempoolSniper()'
)

# Pass telegram service after instantiation
content = content.replace(
    '_copy_engine.telegram_service = _telegram_service',
    '_copy_engine.telegram_service = _telegram_service\n_mempool_sniper.telegram_service = _telegram_service'
)

# Start thread
content = content.replace(
    'threading.Thread(target=_copy_engine.poll, daemon=True).start()',
    'threading.Thread(target=_copy_engine.poll, daemon=True).start()\n    threading.Thread(target=_mempool_sniper.poll, daemon=True).start()'
)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("server.py updated")
