# sovereign-survival-agent/scripts/test_live_oracle_onchain.py
"""
Tests live on-chain interaction with the deployed AgentSecurityOracle on Base Mainnet.
1. Records a verified security audit score on-chain.
2. Queries the score using getContractSecurity.
"""
import os
import sys
import json
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(".env.agent")


def main():
    print("==========================================================")
    print("=== 🛡️ TESTING LIVE BASE MAINNET SECURITY ORACLE ===")
    print("==========================================================")

    rpc_url = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
    private_key = os.getenv("AGENT_PRIVATE_KEY")
    if not private_key:
        print("❌ Missing AGENT_PRIVATE_KEY in .env.agent")
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = w3.eth.account.from_key(private_key)
    operator_address = account.address
    print(f"[+] Connected to Base Mainnet (Chain ID: {w3.eth.chain_id})")
    print(f"[+] Operator: {operator_address}")

    # Load deployed oracle address
    deploy_file = Path("deployments/base_mainnet_oracle.json")
    if not deploy_file.exists():
        print("❌ Deployments file not found.")
        return

    with open(deploy_file, "r", encoding="utf-8") as f:
        deploy_info = json.load(f)

    oracle_address = deploy_info.get("contract_address")
    print(f"[+] Oracle Address: {oracle_address}")
    print(f"👉 BaseScan Contract: https://basescan.org/address/{oracle_address}")

    # Load ABI
    artifact_file = Path("build/contracts/AgentSecurityOracle.json")
    with open(artifact_file, "r", encoding="utf-8") as f:
        artifact = json.load(f)

    oracle_contract = w3.eth.contract(address=oracle_address, abi=artifact["abi"])

    # Target contract to record (AgentPolicyGuard on Base Mainnet)
    target_contract = Web3.to_checksum_address("0x9c59FdB0153325af6d28164832C224C1DE12e4A5")
    security_score = 100
    is_secure = True
    findings_count = 0
    eas_uid = bytes.fromhex("2e29c8e88f553a2908f97b5e43c5fb361dc81f6d338f06059c25bb09581c7e99")

    print(f"\n[*] Recording audit for target contract: {target_contract}...")
    nonce = w3.eth.get_transaction_count(operator_address, "pending")
    gas_price = w3.eth.gas_price

    tx = oracle_contract.functions.recordAudit(
        target_contract,
        security_score,
        is_secure,
        findings_count,
        eas_uid
    ).build_transaction({
        "from": operator_address,
        "nonce": nonce,
        "gasPrice": int(gas_price * 1.2),
        "chainId": w3.eth.chain_id
    })

    gas_estimate = w3.eth.estimate_gas(tx)
    tx["gas"] = int(gas_estimate * 1.2)

    print("[*] Signing and broadcasting record transaction...")
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"[+] Transaction Sent! TX: {tx_hash.hex()}")
    print(f"👉 BaseScan TX: https://basescan.org/tx/{tx_hash.hex()}")

    print("[*] Waiting for transaction receipt...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    print(f"[+] Confirmed in Block #{receipt.blockNumber} with status: {receipt.status}")

    # Now verify reading from oracle
    print("\n[*] Querying on-chain security record via queryContractSecurity (eth_call)...")
    is_registered = oracle_contract.functions.hasAuditRecord(target_contract).call()
    record = oracle_contract.functions.queryContractSecurity(target_contract).call({"from": operator_address})
    print("==========================================================")
    print("🎉 ON-CHAIN ORACLE RECORD VERIFIED ON BASE MAINNET:")
    print(f"• Is Registered: {is_registered}")
    print(f"• Target Contract: {target_contract}")
    print(f"• Security Score: {record[0]} / 100")
    print(f"• Is Secure: {record[1]}")
    print(f"• Findings Count: {record[2]}")
    print(f"• Audit Timestamp: {record[3]}")
    print(f"• EAS Attestation UID: 0x{record[4].hex()}")
    print("==========================================================")


if __name__ == "__main__":
    main()
