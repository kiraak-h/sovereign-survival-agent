import urllib.request, json
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://api.geckoterminal.com/api/v2/networks/base/new_pools', headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
try:
    with urllib.request.urlopen(req, context=ctx) as r:
        data = json.loads(r.read())
        pools = data.get('data', [])
        for p in pools[:5]:
            attrs = p.get('attributes', {})
            base_token_id = p.get('relationships', {}).get('base_token', {}).get('data', {}).get('id', '')
            token_addr = base_token_id.replace('base_', '')
            print(attrs.get('name'), "-", token_addr)
except Exception as e:
    print(e)
