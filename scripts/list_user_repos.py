import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(".env.agent")

token = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

res = requests.get("https://api.github.com/user/repos?type=all&per_page=100", headers=headers)
print("HTTP Status:", res.status_code)
if res.status_code == 200:
    repos = res.json()
    print(f"Total Repositories Found: {len(repos)}")
    for r in repos:
        name = r.get("name")
        is_priv = r.get("private")
        url = r.get("html_url")
        print(f"- {name} (Private: {is_priv}) -> {url}")
