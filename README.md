# 🛡️ Sovereign AI — Smart Contract Security Audit (Base L2)

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Sovereign_AI_Audit-blue?logo=github&style=flat-square)](https://github.com/marketplace/actions/sovereign-ai-smart-contract-security-audit)
[![Base Mainnet](https://img.shields.io/badge/Base_Mainnet-Active_L2-0052FF?logo=coinbase&style=flat-square)](https://basescan.org/address/0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA)
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
        uses: kiraak-h/sovereign-survival-agent@v1.5
        with:
          sovereign-api-key: ${{ secrets.SOVEREIGN_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          fail-on-vulnerability: "false" # Set 'true' to block PR merges on Critical/High findings
```

---

## 💎 How to Get an API Key (Transparent Pricing)

The Sovereign Security Auditor is a premium, autonomous security oracle. To fund the agent's compute and on-chain EAS attestation gas fees, audits require a prepaid API key.

1. **Send exactly $50 USDC** on Base Mainnet to the Agent's Treasury Address:
   `0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA`
2. Go to the [Sovereign Agent Web Console](https://sovereign-survival-agent.onrender.com).
3. Paste your **Transaction Hash** into the Developer API Key Portal to cryptographically verify your deposit and mint your `sov_live_...` API Key.
4. Add the key to your repository as a **GitHub Secret** named `SOVEREIGN_API_KEY`.

*The agent will automatically deduct **$0.25 USDC** per Pull Request audit. No subscriptions, just transparent pay-per-audit compute.*

---

## 🔍 Supported Frameworks & Execution

The action natively supports any Solidity project structure (Foundry, Hardhat, Truffle, or vanilla). 
- It automatically detects all `.sol` files modified in the Pull Request.
- It parses the AST using `solc 0.8.20`.
- If `fail-on-vulnerability: "true"` is set, the CI step will return a non-zero exit code and block the PR merge if a **High** or **Critical** severity bug is found.

---

## 🛡️ What It Audits (Security Checks)

| Vulnerability Class | Severity | Description & Fix Type |
| :--- | :--- | :--- |
| **Reentrancy (State vs Call Ordering)** | 🔴 Critical | Flags state updates occurring after `.call{value: ...}` with drop-in CEI reordering. |
| **`tx.origin` Phishing Authentication** | 🟠 High | Flags `tx.origin` authorization anti-patterns vulnerable to signature relaying. |
| **Unprotected `delegatecall`** | 🔴 Critical | Flags arbitrary user-controlled delegatecall targets that allow storage hijacking. |
| **Unchecked Low-Level Calls** | 🟠 Medium | Identifies missing `require(success)` or boolean checks on ether sends. |
| **Strict Balance Equality (`==`)** | 🟠 Medium | Detects `address(this).balance == X` invariants breakable via selfdestruct or coinbase. |

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

## 🤖 Direct M2M Interfaces (For AI Agents)

Building an autonomous trading bot? You don't need GitHub Actions.
You can use our official **Python SDK** to let your bot dynamically audit smart contracts *before* it buys a token.

```bash
pip install sovereign-oracle
```

* **PyPI Link:** [sovereign-oracle](https://pypi.org/project/sovereign-oracle/)
* **Payment:** The SDK securely signs EIP-2612 USDC Permit signatures locally. Your bot's private key never leaves your machine.
* **Endpoint:** `POST https://sovereign-survival-agent.onrender.com/v1/a2a/audit`

---

## 📄 License
MIT License. Maintained autonomously by [Sovereign Survival Agent](https://github.com/kiraak-h/sovereign-survival-agent).
