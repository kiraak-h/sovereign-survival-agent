# sovereign-survival-agent/scripts/deploy_mainnet.py
"""
Base Mainnet Production Deployment & Verification Script:
Deploys AgentPolicyGuard.sol directly to Base Mainnet (Chain ID 8453),
enforcing daily spend caps on real ETH/USDC and generating live BaseScan records.
"""
from __future__ import annotations
import os
import json
import solcx
from pathlib import Path
from eth_account import Account
from web3 import Web3
from core.network_config import NETWORKS, NetworkMode
from scripts.broadcast_live_tx import get_or_create_agent_wallet


def deploy_to_base_mainnet():
    print("=" * 70)
    print("=== DEPLOYING AGENT POLICY GUARD TO BASE MAINNET (8453) ===")
    print("=" * 70)

    mainnet_spec = NETWORKS[NetworkMode.BASE_MAINNET]
    
    # 1. Connect to Base Mainnet RPC
    w3 = None
    for rpc in mainnet_spec.rpc_urls:
        try:
            temp_w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 6}))
            if temp_w3.is_connected():
                w3 = temp_w3
                print(f"[+] Connected to Base Mainnet RPC: {rpc}")
                break
        except Exception:
            continue

    if not w3:
        print("[!] Could not establish connection to Base Mainnet.")
        return {"status": "RPC_ERROR"}

    # 2. Get Agent Keys
    account, session_account, pk = get_or_create_agent_wallet()
    bal_wei = w3.eth.get_balance(account.address)
    bal_eth = float(w3.from_wei(bal_wei, "ether"))
    print(f"[*] Agent Address: {account.address}")
    print(f"[*] Base Mainnet Balance: {bal_eth:.6f} ETH")

    if bal_eth < 0.0005:
        print(f"[!] Insufficient Base Mainnet ETH for gas. Required: ~0.001 ETH, Available: {bal_eth:.6f} ETH")
        print("    Please fund your address on Base Mainnet to deploy: " + account.address)
        return {
            "status": "AWAITING_GAS_FUNDING",
            "agent_address": account.address,
            "balance_eth": bal_eth,
            "network": "Base Mainnet (8453)"
        }

    # 3. Compile Contract
    contract_file = Path("contracts/AgentPolicyGuard.sol")
    with open(contract_file, "r", encoding="utf-8") as f:
        source = f.read()

    solcx.set_solc_version("0.8.20")
    compiled = solcx.compile_source(source, output_values=["abi", "bin"])
    contract_id = "<stdin>:AgentPolicyGuard"
    abi = compiled[contract_id]["abi"]
    bytecode = compiled[contract_id]["bin"]

    # 4. Deploy Contract
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    daily_limit_wei = w3.to_wei(0.05, "ether")
    nonce = w3.eth.get_transaction_count(account.address)

    tx = contract.constructor(session_account.address, daily_limit_wei).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gasPrice": int(w3.eth.gas_price * 1.2),
        "chainId": 8453
    })

    signed = w3.eth.account.sign_transaction(tx, pk)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"[+] Broadcasted Deployment Tx: 0x{tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    deployed_address = receipt.contractAddress
    print(f"[🎉] AgentPolicyGuard Deployed on Base Mainnet: {deployed_address}")
    print(f"    View on BaseScan: https://basescan.org/address/{deployed_address}")

    # Save to deployments manifest
    out_manifest = Path("deployments/base_mainnet.json")
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(out_manifest, "w", encoding="utf-8") as f:
        json.dump({
            "network": "Base Mainnet",
            "chain_id": 8453,
            "contract_address": deployed_address,
            "tx_hash": f"0x{tx_hash.hex()}",
            "block_number": receipt.blockNumber,
            "master_address": account.address,
            "session_key_address": session_account.address,
            "daily_limit_eth": 0.05,
            "basescan_url": f"https://basescan.org/address/{deployed_address}"
        }, f, indent=2)

    return {
        "status": "DEPLOYED",
        "contract_address": deployed_address,
        "tx_hash": f"0x{tx_hash.hex()}",
        "basescan_url": f"https://basescan.org/address/{deployed_address}"
    }


if __name__ == "__main__":
    deploy_to_base_mainnet()
