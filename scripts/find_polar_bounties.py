# sovereign-survival-agent/scripts/find_polar_bounties.py
import os
import sys
import re
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(".env.agent")

token = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

query = 'is:issue is:open "polar.sh" "reward"'
res = requests.get(
    "https://api.github.com/search/issues",
    params={"q": query, "sort": "created", "order": "desc", "per_page": 20},
    headers=headers,
    timeout=8.0
)

print("Search HTTP Status:", res.status_code)
if res.status_code == 200:
    items = res.json().get("items", [])
    print(f"Total Polar/Bounty Issues Found: {len(items)}\n")
    for item in items[:10]:
        title = item.get("title")
        url = item.get("html_url")
        body = item.get("body") or ""
        
        # Check dollar amounts
        match = re.search(r"\$\s*([0-9]+(?:\.[0-9]{1,2})?)", body)
        reward = match.group(1) if match else "N/A"
        
        repo_match = re.search(r"github\.com/([\w-]+/[\w-]+)", url)
        repo = repo_match.group(1) if repo_match else ""
        
        print(f"• Repo: {repo}")
        print(f"  Title: {title}")
        print(f"  Reward: ${reward}")
        print(f"  URL: {url}")
        print("-" * 50)
