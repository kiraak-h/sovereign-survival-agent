# sovereign-survival-agent/scripts/deploy_policy_guard.py
"""
Live Base Sepolia Smart Contract Deployer & Verifier:
Compiles AgentPolicyGuard.sol using solc 0.8.20, deploys it to Base Sepolia L2 (84532),
funds it with initial ETH, binds the agent session key, and verifies on-chain state.
"""
from __future__ import annotations
import os
import json
import time
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3
import solcx

try:
    from scripts.broadcast_live_tx import (
        get_connected_w3,
        get_or_create_agent_wallet,
        BASE_SEPOLIA_CHAIN_ID,
        BASE_SEPOLIA_EXPLORER,
        BASE_SEPOLIA_USDC
    )
except ImportError:
    from broadcast_live_tx import (
        get_connected_w3,
        get_or_create_agent_wallet,
        BASE_SEPOLIA_CHAIN_ID,
        BASE_SEPOLIA_EXPLORER,
        BASE_SEPOLIA_USDC
    )


# Load environment
load_dotenv(dotenv_path=".env.agent")


def compile_agent_policy_guard() -> tuple[list, str]:
    """Compiles AgentPolicyGuard.sol and exports ABI + Bytecode."""
    solcx.set_solc_version("0.8.20")
    contract_path = Path("contracts/AgentPolicyGuard.sol")
    with open(contract_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    compiled = solcx.compile_source(source_code, output_values=["abi", "bin"])
    contract_key = "<stdin>:AgentPolicyGuard"
    if contract_key not in compiled:
        for k in compiled.keys():
            if "AgentPolicyGuard" in k:
                contract_key = k
                break

    abi = compiled[contract_key]["abi"]
    bytecode = compiled[contract_key]["bin"]

    # Persist ABI and Bytecode for tooling
    with open("contracts/AgentPolicyGuard.abi.json", "w", encoding="utf-8") as f:
        json.dump(abi, f, indent=2)

    with open("contracts/AgentPolicyGuard.bin", "w", encoding="utf-8") as f:
        f.write(bytecode)

    return abi, bytecode


def deploy_policy_guard_to_base_sepolia() -> dict:
    """Deploys AgentPolicyGuard.sol live on Base Sepolia L2."""
    w3, active_rpc = get_connected_w3()
    account, session_acc, pk = get_or_create_agent_wallet()

    print("=" * 70)
    print("=== LIVE BASE SEPOLIA SMART CONTRACT DEPLOYMENT (Chain ID: 84532) ===")
    print("=" * 70)
    print(f"Connected RPC:         {active_rpc}")
    print(f"Deployer (Agent):      {account.address}")
    print(f"Session Key:           {session_acc.address}")

    # Check live balance
    balance_wei = w3.eth.get_balance(account.address)
    balance_eth = float(w3.from_wei(balance_wei, "ether"))
    print(f"Live On-Chain Balance: {balance_eth:.6f} ETH")

    if balance_eth < 0.005:
        raise ValueError(f"Insufficient testnet ETH: {balance_eth:.6f} ETH. Minimum 0.005 ETH required.")

    # 1. Compile contract
    print("\n[1/4] Compiling contracts/AgentPolicyGuard.sol with solc 0.8.20...")
    abi, bytecode = compile_agent_policy_guard()
    print(f"      Bytecode length: {len(bytecode)} characters ({len(bytecode)//2} bytes)")

    # 2. Build deployment transaction
    print("\n[2/4] Constructing deployment transaction...")
    guard_contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    daily_limit = w3.to_wei(0.05, "ether")
    max_tx_limit = w3.to_wei(0.01, "ether")
    initial_vault_funding = w3.to_wei(0.005, "ether")  # Fund the contract vault

    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = int(w3.eth.gas_price * 1.2)  # 20% buffer for fast inclusion

    construct_txn = guard_contract.constructor(
        session_acc.address,
        daily_limit,
        max_tx_limit
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gasPrice": gas_price,
        "value": initial_vault_funding,
        "chainId": BASE_SEPOLIA_CHAIN_ID
    })

    # Estimate gas
    try:
        estimated_gas = w3.eth.estimate_gas(construct_txn)
        construct_txn["gas"] = int(estimated_gas * 1.3)
    except Exception:
        construct_txn["gas"] = 1500000

    print(f"      Gas Limit: {construct_txn['gas']} | Gas Price: {gas_price / 1e9:.2f} Gwei")
    print(f"      Initial Contract Funding: 0.005 ETH")

    # 3. Sign and broadcast
    print("\n[3/4] Signing and broadcasting deployment transaction to Base Sepolia...")
    signed_tx = w3.eth.account.sign_transaction(construct_txn, pk)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_hash_hex = f"0x{tx_hash.hex()}"
    print(f"      Transaction Broadcast Hash: {tx_hash_hex}")
    print(f"      Waiting for block confirmation on Base Sepolia...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=90)
    contract_address = receipt.contractAddress
    print(f"\n[4/4] [SUCCESS] SMART CONTRACT DEPLOYED ON-CHAIN!")
    print(f"      Contract Address:    {contract_address}")
    print(f"      Block Number:        #{receipt.blockNumber}")
    print(f"      Gas Used:            {receipt.gasUsed}")
    print(f"      BaseScan Link:       {BASE_SEPOLIA_EXPLORER}/address/{contract_address}")

    # 4. Verify on-chain contract state
    deployed_instance = w3.eth.contract(address=contract_address, abi=abi)
    onchain_owner = deployed_instance.functions.owner().call()
    onchain_session_key = deployed_instance.functions.agentSessionKey().call()
    onchain_daily_limit = deployed_instance.functions.dailySpendLimit().call()

    print(f"\n=== ON-CHAIN STATE VERIFICATION ===")
    print(f"Verified Owner:        {onchain_owner} (Matches Agent: {onchain_owner == account.address})")
    print(f"Verified Session Key:  {onchain_session_key} (Matches: {onchain_session_key == session_acc.address})")
    print(f"Verified Daily Limit:  {w3.from_wei(onchain_daily_limit, 'ether')} ETH")

    deployment_record = {
        "network": "Base Sepolia Testnet",
        "chain_id": BASE_SEPOLIA_CHAIN_ID,
        "status": "DEPLOYED_LIVE_ON_CHAIN",
        "contract_name": "AgentPolicyGuard",
        "contract_address": contract_address,
        "owner_address": account.address,
        "session_key_address": session_acc.address,
        "daily_limit_eth": float(w3.from_wei(onchain_daily_limit, "ether")),
        "whitelisted_usdc": BASE_SEPOLIA_USDC,
        "tx_hash": tx_hash_hex,
        "block_number": receipt.blockNumber,
        "gas_used": receipt.gasUsed,
        "basescan_url": f"{BASE_SEPOLIA_EXPLORER}/address/{contract_address}",
        "tx_basescan_url": f"{BASE_SEPOLIA_EXPLORER}/tx/{tx_hash_hex}",
        "deployed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Save to deployments manifest
    out_dir = Path("deployments")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "base_sepolia.json", "w", encoding="utf-8") as f:
        json.dump(deployment_record, f, indent=2)

    print(f"[+] Deployment record saved to deployments/base_sepolia.json")
    return deployment_record


if __name__ == "__main__":
    deploy_policy_guard_to_base_sepolia()
