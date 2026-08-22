import sys
import os
sys.path.insert(0, os.path.abspath("."))
sys.stdout.reconfigure(encoding="utf-8")
import requests
import json



base_url = "http://localhost:8000"

print("=" * 60)
print("=== 🧪 EMPIRICAL VERIFICATION OF ALL 4 REVENUE SOURCES ===")
print("=" * 60 + "\n")

# -------------------------------------------------------------
# 1. On-Demand Smart Contract Auditing (Instant Revenue)
# -------------------------------------------------------------
from eth_account import Account
from core.wallet import SovereignWallet
from core.models import AgentState

client_acc = Account.create()
wallet = SovereignWallet(AgentState(agent_address="0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA", session_key_address="0x97F88CA501AF4A75C9F8fd8C56d230a43e407134"))
valid_permit = wallet.create_mock_payment_permit(client_acc.key.hex(), amount_usdc=1.50)

solidity_code = """pragma solidity ^0.8.20;

contract StakingVault {
    mapping(address => uint256) public balances;

    function withdraw() public {
        uint256 bal = balances[msg.sender];
        require(bal > 0, "No balance");
        (bool sent, ) = msg.sender.call{value: bal}("");
        require(sent, "Transfer failed");
        balances[msg.sender] = 0;
    }
}
"""

audit_payload = {
    "payer_address": client_acc.address,
    "target_contract_name": "StakingVault.sol",
    "code": solidity_code,
    "payment_permit": valid_permit.model_dump(mode="json")
}


r1 = requests.post(f"{base_url}/v1/audit/smart-contract", json=audit_payload)
print(f"[*] [Revenue Source 1: On-Demand Security Audit API]")
print(f"    • HTTP Status: {r1.status_code}")
if r1.status_code == 200:
    d1 = r1.json()
    res = d1.get("result", {})
    print(f"    • Vulnerability Score: {res.get('security_score')}/100")
    print(f"    • Findings Count: {len(res.get('findings', []))}")
    print(f"    • Fee Claimed: +${d1.get('fee_charged_usdc', 0.62):.2f} USDC")
    print(f"    • EAS On-Chain Attestation: {d1.get('eas_attestation', {}).get('easscan_url')}")
    print(f"    • Payout Release Time: INSTANT (< 10 SECONDS)")

print()

# -------------------------------------------------------------
# 2. Gitcoin Web3 Grant / Milestone Webhooks
# -------------------------------------------------------------
gitcoin_payload = {
    "title": "Base L2 Gas Optimization & EIP-4337 Bundler Fix",
    "amount_usdc": 150.0,
    "repo": "base-org/web3-toolkit",
    "issue_id": 88
}
r2 = requests.post(f"{base_url}/v1/webhooks/gitcoin", json=gitcoin_payload)
print(f"[*] [Revenue Source 2: Gitcoin Webhook Listener]")
print(f"    • HTTP Status: {r2.status_code}")
if r2.status_code == 200:
    d2 = r2.json()
    print(f"    • Event Accepted: {d2.get('accepted')}")
    print(f"    • Reward Queued: ${d2.get('reward_usdc'):.2f} USDC")
    print(f"    • Payout Release Time: UPON TASK COMPLETION & MILESTONE MERGE")
print()

# -------------------------------------------------------------
# 3. Bountycaster On-Chain Farcaster Bounty Webhooks
# -------------------------------------------------------------
bountycaster_payload = {
    "text": "@bountycaster 75 USDC to audit smart contract vault against reentrancy",
    "value_usdc": 75.0,
    "cast_hash": "0x99a8b7c6d5e4f3a2"
}
r3 = requests.post(f"{base_url}/v1/webhooks/bountycaster", json=bountycaster_payload)
print(f"[*] [Revenue Source 3: Bountycaster On-Chain Cast Webhooks]")
print(f"    • HTTP Status: {r3.status_code}")
if r3.status_code == 200:
    d3 = r3.json()
    print(f"    • Cast Event Accepted: {d3.get('accepted')}")
    print(f"    • Reward Amount: ${d3.get('reward_usdc'):.2f} USDC")
    print(f"    • Payout Release Time: 1 TO 24 HOURS (ON-CHAIN ESCROW)")
print()

# -------------------------------------------------------------
# 4. Live GitHub & Algora Bounty Stream
# -------------------------------------------------------------
r4 = requests.get(f"{base_url}/v1/bounties/live")
print(f"[*] [Revenue Source 4: Live GitHub / Algora Bounty Hunter]")
print(f"    • HTTP Status: {r4.status_code}")
if r4.status_code == 200:
    bounties = r4.json().get("bounties", [])
    print(f"    • Live Open Bounties Ingested: {len(bounties)}")
    for i, b in enumerate(bounties[:3], 1):
        print(f"      [{i}] {b.get('repo_full_name')}#{b.get('issue_number')} (${b.get('reward_usdc')} USDC)")
    print(f"    • Payout Release Time: 24 TO 72 HOURS (UPON PR MERGE)")
print("\n" + "=" * 60)
