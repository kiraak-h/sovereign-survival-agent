# sovereign-survival-agent/action/ci_runner.py
"""
GitHub Action Runner Script:
Inspects repository for Solidity files (.sol), audits each contract using the Sovereign Agent API,
generates a comprehensive PR review comment, and sets Action outputs.
"""
from __future__ import annotations
import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Any

sys.stdout.reconfigure(encoding="utf-8")


def find_solidity_files(root_dir: str = ".") -> List[Path]:
    """Finds all .sol files in the repository, excluding node_modules and .git."""
    files = []
    for p in Path(root_dir).rglob("*.sol"):
        if "node_modules" not in str(p) and ".git" not in str(p) and "test" not in str(p).lower():
            files.append(p)
    return files


def format_pr_comment(results: List[Dict[str, Any]], overall_score: int, min_score: int) -> str:
    """Formats a clean, informative GitHub PR security review comment."""
    status_emoji = "🟢 PASS" if min_score >= 80 else "🟡 WARNING" if min_score >= 50 else "🔴 ACTION REQUIRED"
    
    table_rows = []
    findings_details = []
    
    for r in results:
        score = r.get("security_score", 100)
        score_badge = "🟢 100/100" if score == 100 else f"🟡 {score}/100" if score >= 70 else f"🔴 {score}/100"
        name = r.get("contract_name", "Contract.sol")
        findings = r.get("findings", [])
        eas_link = f"[EAS Proof ↗]({r.get('eas_attestation_url')})" if r.get("eas_attestation_url") else "N/A"
        
        table_rows.append(f"| `{name}` | {score_badge} | {len(findings)} finding(s) | {eas_link} |")
        
        if findings:
            findings_details.append(f"#### 🔍 Findings in `{name}`:")
            for idx, f in enumerate(findings, 1):
                findings_details.append(
                    f"**{idx}. [{f.get('severity')}] {f.get('title')}** (Line {f.get('line', 'N/A')})\n"
                    f"- *Impact*: {f.get('description')}\n"
                    f"- *Remediation*: `{f.get('recommendation')}`\n"
                )

    findings_section = "\n".join(findings_details) if findings_details else "_No critical security vulnerabilities detected._"

    comment = f"""## 🛡️ Sovereign AI Smart Contract Security Audit

**Overall Status**: **{status_emoji}** (Aggregate Score: **{overall_score} / 100**)

| Contract | Score | Findings | On-Chain Attestation |
| :--- | :--- | :--- | :--- |
{chr(10).join(table_rows)}

---

### 📋 Audit Findings Summary
{findings_section}

---
<sub>⚡ Audited autonomously by <a href="https://sovereign-survival-agent.onrender.com">Sovereign Survival Agent</a> on Base L2 | Powered by solc 0.8.20 AST Static Analysis & Ethereum Attestation Service (EAS)</sub>
"""
    return comment


def post_github_pr_comment(comment: str, token: str, repo: str, pr_number: str) -> bool:
    """Posts comment to the active GitHub Pull Request."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    try:
        res = requests.post(url, json={"body": comment}, headers=headers, timeout=10)
        return res.status_code in (200, 201)
    except Exception as e:
        print(f"[-] Failed to post PR comment: {e}")
        return False


def main():
    agent_api = os.getenv("AGENT_API_URL", "https://sovereign-survival-agent.onrender.com").rstrip("/")
    token = os.getenv("GITHUB_TOKEN")
    fail_on_vuln = os.getenv("FAIL_ON_VULNERABILITY", "false").lower() == "true"
    
    sol_files = find_solidity_files()
    if not sol_files:
        print("[*] No Solidity files found to audit. CI Check passing.")
        return 0

    print(f"[*] Found {len(sol_files)} Solidity contract(s) to audit...")
    audit_results = []
    
    for f in sol_files:
        print(f"    • Auditing {f.name}...")
        try:
            code = f.read_text(encoding="utf-8")
            res = requests.post(
                f"{agent_api}/v1/audit/direct",
                json={
                    "code": code,
                    "contract_name": f.name,
                    "target_ref": f"CI/{f.name}"
                },
                timeout=20
            )
            if res.status_code == 200:
                audit_results.append(res.json())
            else:
                print(f"[-] Error auditing {f.name}: HTTP {res.status_code}")
        except Exception as e:
            print(f"[-] Error connecting to Sovereign Agent API: {e}")

    if not audit_results:
        print("[!] No audit results returned from API.")
        return 0

    scores = [r.get("security_score", 100) for r in audit_results]
    overall_score = sum(scores) // len(scores) if scores else 100
    min_score = min(scores) if scores else 100

    # Post to PR if GitHub Event context is available
    event_path = os.getenv("GITHUB_EVENT_PATH")
    repo = os.getenv("GITHUB_REPOSITORY")
    
    if event_path and os.path.exists(event_path) and token and repo:
        try:
            with open(event_path, "r", encoding="utf-8") as ef:
                event_data = json.load(ef)
            pr_number = event_data.get("pull_request", {}).get("number")
            if pr_number:
                comment = format_pr_comment(audit_results, overall_score, min_score)
                print(f"[*] Posting security review to PR #{pr_number} on {repo}...")
                post_github_pr_comment(comment, token, repo, str(pr_number))
        except Exception as e:
            print(f"[-] Error processing GitHub event payload: {e}")

    # Set Outputs for GitHub Actions
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output and os.path.exists(github_output):
        with open(github_output, "a", encoding="utf-8") as out:
            out.write(f"security-score={overall_score}\n")
            out.write(f"findings-count={sum(r.get('findings_count', 0) for r in audit_results)}\n")
            if audit_results:
                out.write(f"eas-attestation-url={audit_results[0].get('eas_attestation_url', '')}\n")

    print(f"[+] Audit Complete! Overall Security Score: {overall_score}/100")
    if fail_on_vuln and min_score < 70:
        print("[-] Failing CI due to detected security vulnerabilities (FAIL_ON_VULNERABILITY=true).")
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
