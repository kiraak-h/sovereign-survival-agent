import sys

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'from core.mempool_sniper import MempoolSniper',
    'from core.mempool_sniper import MempoolSniper\nfrom core.anti_rug_engine import AntiRugEngine'
)

content = content.replace(
    '_mempool_sniper = MempoolSniper()',
    '_mempool_sniper = MempoolSniper()\n_anti_rug_engine = AntiRugEngine()'
)

content = content.replace(
    '_mempool_sniper.telegram_service = _telegram_service',
    '_mempool_sniper.telegram_service = _telegram_service\n_anti_rug_engine.telegram_service = _telegram_service'
)

content = content.replace(
    'threading.Thread(target=_mempool_sniper.poll, daemon=True).start()',
    'threading.Thread(target=_mempool_sniper.poll, daemon=True).start()\n    threading.Thread(target=_anti_rug_engine.poll, daemon=True).start()'
)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("server.py updated")
