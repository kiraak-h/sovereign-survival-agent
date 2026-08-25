import urllib.request, json, ssl, time
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://api.geckoterminal.com/api/v2/networks/base/new_pools', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx) as r:
    pools = json.loads(r.read()).get('data', [])[:3]
    
tokens = [p.get('relationships', {}).get('base_token', {}).get('data', {}).get('id', '').replace('base_', '') for p in pools]

g_url = f"https://api.gopluslabs.io/api/v1/token_security/8453?contract_addresses={','.join(tokens)}"
g_req = urllib.request.Request(g_url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(g_req, context=ctx) as gr:
    g_data = json.loads(gr.read()).get('result', {})

for t in tokens:
    res = g_data.get(t.lower(), {})
    hp = res.get('is_honeypot') == '1' or res.get('cannot_sell_all') == '1'
    print(t, "Honeypot:", hp)
