# sovereign-survival-agent/scripts/inspect_sendly_issues.py
import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(".env.agent")

token = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

for num in [90, 86, 91]:
    res = requests.get(f"https://api.github.com/repos/Hazyshades/Sendly-Test-Repo/issues/{num}", headers=headers)
    if res.status_code == 200:
        d = res.json()
        title = d.get("title")
        state = d.get("state")
        body = d.get("body")
        print(f"=== Issue #{num}: {title} ===")
        print(f"State: {state}")
        print(f"Body:\n{body}\n")
        
        c_res = requests.get(f"https://api.github.com/repos/Hazyshades/Sendly-Test-Repo/issues/{num}/comments", headers=headers)
        if c_res.status_code == 200:
            print("Comments:")
            for c in c_res.json():
                user = c.get("user", {}).get("login")
                c_body = c.get("body", "").strip()
                print(f"- @{user}: {c_body}")
        print("=" * 60)
