import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://api.geckoterminal.com/api/v2/networks/base/new_pools', headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
    res_data = json.loads(r.read())
    pools = res_data.get('data', [])[:5]

for p in pools:
    attrs = p.get('attributes', {})
    chg_dict = attrs.get('price_change_percentage')
    print("Price change dict:", chg_dict)
    
    if chg_dict is None:
        print("IT IS NONE!")
