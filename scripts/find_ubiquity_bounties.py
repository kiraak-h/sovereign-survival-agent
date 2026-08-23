# sovereign-survival-agent/scripts/find_ubiquity_bounties.py
import os
import sys
import re
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(".env.agent")

token = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

queries = [
    'org:ubiquity-os is:issue is:open "Price:"',
    'org:ubiquity is:issue is:open "Price:"',
    'label:"price: "'
]

print("[*] Searching for live Ubiquity DevPool open bounties...")
for q in queries:
    res = requests.get(
        "https://api.github.com/search/issues",
        params={"q": q, "sort": "created", "order": "desc", "per_page": 10},
        headers=headers,
        timeout=8.0
    )
    if res.status_code == 200:
        items = res.json().get("items", [])
        print(f"Query '{q}' returned {len(items)} issues:")
        for item in items[:5]:
            title = item.get("title")
            url = item.get("html_url")
            labels = [l.get("name") for l in item.get("labels", []) if isinstance(l, dict)]
            print(f"- Title: {title}")
            print(f"  Labels: {labels}")
            print(f"  URL: {url}")
            print("---")
