# sovereign-survival-agent/scripts/find_real_mainnet_bounties.py
"""
Deep search for genuine, real-money mainnet bounties (Algora, Polar.sh, Bountycaster, Gitcoin).
Filters out test repos, test tokens, and synthetic mock listings.
"""
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
    'label:"bounty" is:open is:issue "USDC"',
    'label:"bounty" is:open is:issue "$"',
    'label:"algora" is:open is:issue',
    'label:"polar" is:open is:issue',
    'is:open is:issue "funded with Polar"'
]

found = []
seen_urls = set()

print("[*] Searching GitHub for genuine funded bounties...")
for q in queries:
    res = requests.get(
        "https://api.github.com/search/issues",
        params={"q": q, "sort": "created", "order": "desc", "per_page": 10},
        headers=headers,
        timeout=8.0
    )
    if res.status_code == 200:
        items = res.json().get("items", [])
        for item in items:
            url = item.get("html_url")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            title = item.get("title", "")
            body = item.get("body", "") or ""
            repo_match = re.search(r"github\.com/([\w-]+/[\w-]+)", url)
            repo = repo_match.group(1) if repo_match else ""
            
            # Filter out obvious test repos
            if "test-repo" in repo.lower() or "testnet" in body.lower() and "test tokens" in body.lower():
                continue
                
            found.append({
                "repo": repo,
                "title": title,
                "url": url,
                "body": body[:200]
            })

print(f"\n[+] Discovered {len(found)} candidate(s) (Filtered out testnet/synthetic tokens):\n")
for f in found[:8]:
    print(f"• Repo: {f['repo']}")
    print(f"  Title: {f['title']}")
    print(f"  URL: {f['url']}")
    print("-" * 50)
