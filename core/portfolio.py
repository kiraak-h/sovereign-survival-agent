"""
Real Wallet Balance Engine — Phase A3
Replaces fake portfolio with live Base RPC calls for:
  - ETH balance (eth_getBalance)
  - ERC-20 token balances via DexScreener price data
"""
import json
import ssl
import urllib.request

BASE_RPC = "https://mainnet.base.org"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE

# ERC-20 balanceOf(address) ABI selector
BALANCE_OF_SELECTOR = "0x70a08231"
# ERC-20 decimals() selector
DECIMALS_SELECTOR = "0x313ce567"
# ERC-20 symbol() selector
SYMBOL_SELECTOR = "0x95d89b41"


def _rpc(method: str, params: list) -> dict:
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode()
    req = urllib.request.Request(BASE_RPC, data=payload, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=12, context=_ctx) as r:
        return json.loads(r.read())


def _call(to: str, data: str) -> str:
    resp = _rpc("eth_call", [{"to": to, "data": data}, "latest"])
    return resp.get("result", "0x")


def get_eth_balance(address: str) -> float:
    """Returns the real ETH balance of an address on Base Mainnet."""
    resp = _rpc("eth_getBalance", [address, "latest"])
    return int(resp.get("result", "0x0"), 16) / 1e18


def get_erc20_balance(wallet: str, token: str) -> float:
    """Returns the raw ERC-20 token balance."""
    padded_wallet = "000000000000000000000000" + wallet[2:]
    data = BALANCE_OF_SELECTOR + padded_wallet
    result = _call(token, data)
    if result == "0x" or not result:
        return 0.0
    return int(result, 16)


def get_erc20_decimals(token: str) -> int:
    result = _call(token, DECIMALS_SELECTOR)
    if result == "0x" or not result:
        return 18
    return int(result, 16)


def get_portfolio_positions(address: str, known_tokens: list = None) -> list:
    """
    Returns real portfolio positions for the given wallet address.

    For now, checks a curated list of popular Base tokens.
    In production this would use an indexer (Moralis/Alchemy).
    """
    # Popular Base ecosystem tokens to check
    BASE_TOKENS = [
        {"address": "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed", "symbol": "DEGEN"},
        {"address": "0x8f0cb368c63fbedf7ff49f16f49c3eb5140d04fb", "symbol": "TOSHI"},
        {"address": "0x532f27101965dd16442e59d40670faf5ebb142e4", "symbol": "BRETT"},
        {"address": "0xac1bd2486aaf3b5c0fc3fd868558b082a531b2b4", "symbol": "TYBG"},
        {"address": "0x0d97f261b1e88845184f678e2d1e7a98d9fd38de", "symbol": "VIRTUAL"},
    ]

    if known_tokens:
        BASE_TOKENS = known_tokens

    positions = []
    for token_info in BASE_TOKENS:
        try:
            token_addr = token_info["address"]
            decimals = get_erc20_decimals(token_addr)
            raw_balance = get_erc20_balance(address, token_addr)
            if raw_balance == 0:
                continue
            balance = raw_balance / (10 ** decimals)

            # Get price from DexScreener
            try:
                dex_url = "https://api.dexscreener.com/latest/dex/tokens/" + token_addr
                req = urllib.request.Request(dex_url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=10, context=_ctx) as r:
                    dex = json.loads(r.read())
                pairs = dex.get("pairs") or []
                if pairs:
                    pairs.sort(key=lambda p: p.get("liquidity", {}).get("usd", 0) or 0, reverse=True)
                    price_usd = float(pairs[0].get("priceUsd", 0) or 0)
                else:
                    price_usd = 0.0
            except Exception:
                price_usd = 0.0

            value_usd = balance * price_usd

            # Anti-dust: skip tokens worth less than $1.00
            if value_usd < 1.0:
                continue

            positions.append({
                "symbol": token_info.get("symbol", "?"),
                "address": token_addr,
                "balance": round(balance, 4),
                "value_usd": round(value_usd, 2),
                "pnl_pct": 0.0,  # Real PnL needs buy price history from DB
            })
        except Exception:
            continue

    return positions
