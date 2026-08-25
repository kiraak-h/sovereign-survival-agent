"""
Real Token Scanner — Phase A1
Replaces the random() simulator with live data from:
  - honeypot.is  (honeypot check, buy/sell tax, holder count)
  - DexScreener  (price, liquidity USD, market cap)
  - Base RPC     (contract code existence = deployed check)
"""
import json
import ssl
import urllib.request

BASE_RPC = "https://mainnet.base.org"
HONEYPOT_API = "https://api.honeypot.is/v2/IsHoneypot"
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=12, context=_ctx) as r:
        return json.loads(r.read())


def _rpc(method: str, params: list) -> dict:
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode()
    req = urllib.request.Request(BASE_RPC, data=payload, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=12, context=_ctx) as r:
        return json.loads(r.read())


class TokenScanner:

    def scan(self, token_address: str) -> dict:
        token_address = token_address.lower()
        result = {
            "symbol": "UNKNOWN",
            "name": "Unknown Token",
            "is_honeypot": False,
            "is_verified": False,
            "buy_tax": 0.0,
            "sell_tax": 0.0,
            "liquidity_eth": 0.0,
            "market_cap_usd": 0.0,
            "holder_count": 0,
            "top_10_holders_pct": 0.0,
            "deployer_age_days": 0,
            "deployer_tx_count": 0,
            "lp_locked": False,
            "lp_lock_days": 0,
            "verdict": "UNKNOWN",
            "risk_score": 50,
            "error": None,
        }

        # --- 1. honeypot.is ---
        try:
            hp_data = _get(f"{HONEYPOT_API}?address={token_address}&chainID=8453")
            token_meta = hp_data.get("token", {})
            result["symbol"] = token_meta.get("symbol", "?")
            result["name"] = token_meta.get("name", "?")
            result["holder_count"] = token_meta.get("totalHolders", 0)

            hp_result = hp_data.get("honeypotResult", {})
            result["is_honeypot"] = hp_result.get("isHoneypot", False)

            sim = hp_data.get("simulationResult", {})
            result["buy_tax"] = round(sim.get("buyTax", 0.0) or 0.0, 2)
            result["sell_tax"] = round(sim.get("sellTax", 0.0) or 0.0, 2)

            summary = hp_data.get("summary", {})
            risk_level = summary.get("riskLevel", 1)  # 1=low, 2=medium, 3=high
        except Exception as e:
            result["error"] = f"honeypot.is: {e}"
            risk_level = 2

        # --- 2. DexScreener ---
        try:
            dex_data = _get(f"{DEXSCREENER_API}/{token_address}")
            pairs = dex_data.get("pairs") or []
            # Pick the pair with highest liquidity
            if pairs:
                pairs.sort(key=lambda p: p.get("liquidity", {}).get("usd", 0) or 0, reverse=True)
                best = pairs[0]
                liq_usd = best.get("liquidity", {}).get("usd", 0) or 0
                price_eth = float(best.get("priceNative", 0) or 0)
                # Convert liquidity USD to ETH using approximate ETH price
                eth_price_approx = 2500.0
                result["liquidity_eth"] = round(liq_usd / eth_price_approx, 2)
                result["market_cap_usd"] = best.get("fdv", 0) or 0
                # If symbol still unknown, pull from dexscreener
                if result["symbol"] == "?":
                    result["symbol"] = best.get("baseToken", {}).get("symbol", "?")
        except Exception as e:
            if result["error"]:
                result["error"] += f" | dexscreener: {e}"
            else:
                result["error"] = f"dexscreener: {e}"

        # --- 3. Base RPC — check contract exists ---
        try:
            code_resp = _rpc("eth_getCode", [token_address, "latest"])
            code = code_resp.get("result", "0x")
            result["is_verified"] = len(code) > 10  # has bytecode = deployed
        except Exception:
            pass

        # --- Risk Scoring ---
        risk = 0
        if result["is_honeypot"]:
            risk += 100
        if result["buy_tax"] > 10:
            risk += 25
        elif result["buy_tax"] > 5:
            risk += 10
        if result["sell_tax"] > 10:
            risk += 25
        elif result["sell_tax"] > 5:
            risk += 10
        if result["liquidity_eth"] < 1.0:
            risk += 20
        if result["holder_count"] < 100:
            risk += 15
        if not result["is_verified"]:
            risk += 10
        if risk_level == 3:
            risk += 20
        elif risk_level == 2:
            risk += 10

        risk = min(risk, 100)
        result["risk_score"] = risk

        if result["is_honeypot"] or risk >= 80:
            result["verdict"] = "DANGER"
        elif risk >= 50:
            result["verdict"] = "RISKY"
        elif risk >= 25:
            result["verdict"] = "MODERATE"
        else:
            result["verdict"] = "SAFE"

        return result
