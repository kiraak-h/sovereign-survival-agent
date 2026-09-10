import os
import re

filepath = 'core/dex_router.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace execute_snipe def
content = content.replace(
    "def execute_snipe(private_key: str, token_address: str, amount_eth: float) -> dict:",
    "def execute_snipe(private_key: str, token_address: str, amount_eth: float, mev_tip_eth: float = 0.0) -> dict:"
)

# Patch execute_snipe tx build
tx_build_snipe = '''
        gas_limit = 300000
        # Build transaction
        tx = {
            "chainId": chain_id,
            "to": UNISWAP_V2_ROUTER,
            "value": trade_wei,
            "gas": gas_limit,
            "nonce": nonce,
            "data": "0x" + calldata.hex(),
        }
        if mev_tip_eth > 0:
            tip_per_gas = int(mev_tip_eth * 1e18) // gas_limit
            tx["maxPriorityFeePerGas"] = tip_per_gas
            tx["maxFeePerGas"] = gas_price + tip_per_gas
        else:
            tx["gasPrice"] = gas_price
'''
content = content.replace('''
        # Build transaction
        tx = {
            "chainId": chain_id,
            "to": UNISWAP_V2_ROUTER,
            "value": trade_wei,
            "gas": 300000,
            "gasPrice": gas_price,
            "nonce": nonce,
            "data": "0x" + calldata.hex(),
        }''', tx_build_snipe)

# Replace execute_partial_sell def
content = content.replace(
    "def execute_partial_sell(private_key: str, token: str, pct: int) -> dict:",
    "def execute_partial_sell(private_key: str, token: str, pct: int, mev_tip_eth: float = 0.0) -> dict:"
)

# Patch execute_partial_sell tx build for approve
approve_build = '''
        approve_gas_limit = 100000
        approve_tx = {
            "chainId": chain_id, "to": token,
            "value": 0, "gas": approve_gas_limit,
            "nonce": nonce,
            "data": approve_data,
        }
        if mev_tip_eth > 0:
            # We don't bribe heavily on approve, just slight bump
            approve_tx["gasPrice"] = int(gas_price * 1.5)
        else:
            approve_tx["gasPrice"] = gas_price
'''
content = content.replace('''
        approve_tx = {
            "chainId": chain_id, "to": token,
            "value": 0, "gas": 100000,
            "gasPrice": gas_price, "nonce": nonce,
            "data": approve_data,
        }''', approve_build)

# Patch execute_partial_sell tx build for swap
swap_build = '''
        swap_gas_limit = 300000
        swap_tx = {
            "chainId": chain_id, "to": UNISWAP_V2_ROUTER,
            "value": 0, "gas": swap_gas_limit,
            "nonce": nonce + 1,
            "data": swap_data,
        }
        if mev_tip_eth > 0:
            tip_per_gas = int(mev_tip_eth * 1e18) // swap_gas_limit
            swap_tx["maxPriorityFeePerGas"] = tip_per_gas
            swap_tx["maxFeePerGas"] = gas_price + tip_per_gas
        else:
            swap_tx["gasPrice"] = gas_price
'''
content = content.replace('''
        swap_tx = {
            "chainId": chain_id, "to": UNISWAP_V2_ROUTER,
            "value": 0, "gas": 300000,
            "gasPrice": gas_price, "nonce": nonce + 1,
            "data": swap_data,
        }''', swap_build)

# Replace execute_sell def
content = content.replace(
    "def execute_sell(private_key: str, token_address: str, percentage: float = 100.0) -> dict:",
    "def execute_sell(private_key: str, token_address: str, percentage: float = 100.0, mev_tip_eth: float = 0.0) -> dict:"
)
content = content.replace(
    "return execute_partial_sell(private_key, token_address, pct)",
    "return execute_partial_sell(private_key, token_address, pct, mev_tip_eth)"
)

# Update the returned dict in snipe
content = content.replace(
    '''"mev_bribe_eth": 0.0,''',
    '''"mev_bribe_eth": mev_tip_eth,'''
)


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated dex_router.py")
