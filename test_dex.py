import urllib.request, json
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://api.dexscreener.com/token-profiles/latest/v1', headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, context=ctx) as r:
        data = json.loads(r.read())
        base_tokens = [t for t in data if t.get('chainId') == 'base']
        print(f"Found {len(base_tokens)} Base tokens out of {len(data)}")
        for t in base_tokens[:5]:
            print(f"{t.get('tokenAddress')}")
except Exception as e:
    print(e)
