# sovereign-survival-agent/scripts/publish_release.py
import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(".env.agent")

token = os.getenv("GITHUB_TOKEN")
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"
}

payload = {
    "tag_name": "v1.0.0",
    "target_commitish": "main",
    "name": "v1.0.0 — Sovereign AI Smart Contract Security Audit",
    "body": """## 🛡️ Sovereign AI Smart Contract Security Audit (v1.0.0)

Drop-in GitHub Action for autonomous static AST and solc 0.8.20 security audits on every Pull Request with on-chain EAS attestations on Base L2.

### ⚡ 1-Line Setup
```yaml
- name: Run Sovereign Security Audit
  uses: kiraak-h/sovereign-survival-agent@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 🔍 Features
- Static AST & solc 0.8.20 vulnerability analysis (Reentrancy, tx.origin, delegatecall, unchecked transfers)
- Automated Pull Request review comments with copy-paste remediation diffs
- Cryptographic Ethereum Attestation Service (EAS) certificates on Base L2
""",
    "draft": False,
    "prerelease": False
}

res = requests.post("https://api.github.com/repos/kiraak-h/sovereign-survival-agent/releases", json=payload, headers=headers)
print("Release HTTP Status:", res.status_code)
if res.status_code in (200, 201):
    d = res.json()
    print("[+] Release Created Successfully!")
    print("👉 Release URL:", d.get("html_url"))
else:
    print("Response:", res.text)
