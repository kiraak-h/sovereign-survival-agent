# 🛡️ Sovereign AI — Smart Contract Security Audit (Base L2)

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Sovereign_AI_Audit-blue?logo=github&style=flat-square)](https://github.com/marketplace/actions/sovereign-ai-smart-contract-security-audit)
[![Base Mainnet](https://img.shields.io/badge/Base_Mainnet-Active_L2-0052FF?logo=coinbase&style=flat-square)](https://basescan.org/address/0x9c59FdB0153325af6d28164832C224C1DE12e4A5)
[![EAS Attested](https://img.shields.io/badge/EAS_Attested-Base_L2-brightgreen?style=flat-square)](https://base-sepolia.easscan.org)
[![Tests](https://img.shields.io/badge/Tests-61%20Passed%20(100%25)-success?style=flat-square)](https://github.com/kiraak-h/sovereign-survival-agent)

An autonomous, continuous smart contract security auditor for Solidity on **Base L2**. Integrates directly into your GitHub CI/CD pipeline to analyze Pull Requests using **`solc 0.8.20`** AST static analysis, generates copy-paste remediation diffs, and issues cryptographic on-chain **Ethereum Attestation Service (EAS)** certificates.

---

## ⚡ Quick Start: 1-Line GitHub Actions Integration

Create `.github/workflows/security-audit.yml` in your repository:

```yaml
name: "Smart Contract Security Audit"

on:
  pull_request:
    branches: [ "main", "master" ]
  push:
    branches: [ "main", "master" ]

jobs:
  audit:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run Sovereign Security Audit
        uses: kiraak-h/sovereign-survival-agent@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          fail-on-vulnerability: "false" # Set 'true' to block PR merges on Critical/High findings
```

---

## 🔍 What It Audits (Security Checks)

| Vulnerability Class | Severity | Description & Fix Type |
| :--- | :--- | :--- |
| **Reentrancy (State vs Call Ordering)** | 🔴 Critical | Flags state updates occurring after `.call{value: ...}` with drop-in CEI reordering. |
| **`tx.origin` Phishing Authentication** | 🟠 High | Flags `tx.origin` authorization anti-patterns vulnerable to signature relaying. |
| **Unprotected `delegatecall`** | 🔴 Critical | Flags arbitrary user-controlled delegatecall targets that allow storage hijacking. |
| **Unchecked Low-Level Calls** | 🟡 Medium | Identifies missing `require(success)` or boolean checks on ether sends. |
| **Strict Balance Equality (`==`)** | 🟡 Medium | Detects `address(this).balance == X` invariants breakable via selfdestruct or coinbase. |

---

## 💬 Example PR Security Review Output

When a developer opens a Pull Request, the Action automatically comments:

> ## 🛡️ Sovereign AI Smart Contract Security Audit
> **Overall Status**: **🟢 PASS** (Aggregate Score: **100 / 100**)
> 
> | Contract | Score | Findings | On-Chain Attestation |
> | :--- | :--- | :--- | :--- |
> | `StakingVault.sol` | 🟢 100/100 | 0 finding(s) | [EAS Proof ↗](https://base-sepolia.easscan.org/attestation/view/0x2e29...) |
> 
> ---
> <sub>⚡ Audited autonomously by [Sovereign Survival Agent](https://sovereign-survival-agent.onrender.com) on Base L2 | Powered by solc 0.8.20 AST Static Analysis & Ethereum Attestation Service (EAS)</sub>

---

## 🤖 Direct Interfaces

* **Telegram Bot**: Audit any Solidity file instantly via **[@kiraak_survival_agent_bot](https://t.me/kiraak_survival_agent_bot)** (`/audit_scan`, `/audit_repo <url>`).
* **Agent-to-Agent (A2A) API**: Call `POST /v1/a2a/audit` with an EIP-2612 permit for automated machine-to-machine contract verification.
* **On-Chain Base Security Oracle**: Query `AgentSecurityOracle.sol` on Base Mainnet directly from Solidity smart contracts.

---

## 🧪 Local Verification

```bash
# Run 61 comprehensive tests
python -m pytest tests/ -v

# Run local BaseScan & bounty audit sweep
python scripts/test_all_revenue_sources.py
```

---

## 📜 License
MIT License. Maintained autonomously by [Sovereign Survival Agent](https://github.com/kiraak-h/sovereign-survival-agent).
