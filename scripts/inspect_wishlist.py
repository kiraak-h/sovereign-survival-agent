import os
import requests
from dotenv import load_dotenv

load_dotenv(".env.agent")
token = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

for num in [76, 78]:
    r = requests.get(f"https://api.github.com/repos/ubiquity-os/plugins-wishlist/issues/{num}", headers=headers)
    d = r.json()
    title = d.get("title")
    labels = [l.get("name") for l in d.get("labels", [])]
    body = d.get("body", "")
    print(f"=== #{num}: {title} ===")
    print(f"Labels: {labels}")
    print(f"Body:\n{body[:500]}\n---")
