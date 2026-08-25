import json
import urllib.request
import ssl

def check_honeypot(token_address: str) -> bool:
    """Uses DexScreener / GoPlus API to check if a token is a real honeypot.
    Returns True if it's safe, False if it's a honeypot."""
    try:
        url = f"https://api.gopluslabs.io/api/v1/token_security/8453?contract_addresses={token_address}"
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
            data = json.loads(r.read())
            
        res = data.get('result', {}).get(token_address.lower())
        if not res:
            return True # Unknown
            
        is_honeypot = res.get('is_honeypot', '0')
        can_sell = res.get('cannot_sell_all', '0')
        if is_honeypot == '1' or can_sell == '1':
            return False
        return True
    except Exception:
        return True
