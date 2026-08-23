import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(".env.agent")

token = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

for num in [90, 86, 88, 89, 93, 94]:
    res = requests.get(f"https://api.github.com/repos/Hazyshades/Sendly-Test-Repo/issues/{num}", headers=headers)
    if res.status_code == 200:
        d = res.json()
        title = d.get("title")
        cmts = d.get("comments")
        state = d.get("state")
        print(f"Issue #{num} (Comments: {cmts}, State: {state}): {title}")
