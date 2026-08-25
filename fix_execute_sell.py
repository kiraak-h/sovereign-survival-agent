import sys

with open('core/dex_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add execute_sell as an alias for execute_partial_sell at 100%
execute_sell_fn = '''

def execute_sell(private_key: str, token_address: str, percentage: float = 100.0) -> dict:
    """Alias used by limit_engine: sells a percentage of a token bag."""
    pct = int(percentage)
    return execute_partial_sell(private_key, token_address, pct)
'''

content += execute_sell_fn

with open('core/dex_router.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("execute_sell added")
