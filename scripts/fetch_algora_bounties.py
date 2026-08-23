# sovereign-survival-agent/scripts/fetch_algora_bounties.py
import requests
import json

url = "https://api.algora.io/v1/bounties"
try:
    res = requests.get(url, params={"status": "active", "limit": 15}, timeout=6.0)
    print("Algora HTTP Status:", res.status_code)
    if res.status_code == 200:
        data = res.json()
        print(f"Total Algora bounties returned: {len(data.get('items', data if isinstance(data, list) else []))}")
        items = data.get('items', data if isinstance(data, list) else [])
        for item in items[:10]:
            print(f"- Title: {item.get('title')}")
            print(f"  Amount: ${item.get('reward_usd', item.get('amount_usd', 0))} USD")
            print(f"  URL: {item.get('url', item.get('issue_url'))}")
            print("---")
    else:
        print("Response:", res.text[:200])
except Exception as e:
    print("Error querying Algora:", e)
