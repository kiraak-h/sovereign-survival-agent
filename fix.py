import re
with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('from core.ast_analyzer import SovereignASTAnalyzer', 'from core.ast_analyzer import SovereignASTAnalyzer\nfrom core.sniper_wallet import get_or_create_wallet\nfrom core.dex_router import execute_snipe')
