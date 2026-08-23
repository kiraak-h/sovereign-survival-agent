# sovereign-survival-agent/scripts/deploy_oracle_mainnet.py
"""
Deploys AgentSecurityOracle.sol to Base Mainnet (Chain ID 8453).
"""
import os
import sys
import json
import solcx
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(".env.agent")


def compile_oracle_contract():
    contract_path = Path("contracts/AgentSecurityOracle.sol")
    source_code = contract_path.read_text(encoding="utf-8")
    
    solc_v = "0.8.20"
    if solc_v not in [str(v) for v in solcx.get_installed_solc_versions()]:
        solcx.install_solc(solc_v)

    compiled = solcx.compile_source(
        source_code,
        output_values=["abi", "bin"],
        solc_version=solc_v
    )

    contract_id = "<stdin>:AgentSecurityOracle"
    if contract_id not in compiled:
        contract_id = list(compiled.keys())[0]

    abi = compiled[contract_id]["abi"]
    bytecode = compiled[contract_id]["bin"]
    return abi, bytecode


def main():
    print("==========================================================")
    print("=== 🚀 DEPLOYING AGENT SECURITY ORACLE TO BASE MAINNET ===")
    print("==========================================================")

    rpc_url = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
    private_key = os.getenv("AGENT_PRIVATE_KEY")
    if not private_key:
        print("❌ Missing AGENT_PRIVATE_KEY in .env.agent")
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"❌ Failed to connect to Base RPC: {rpc_url}")
        return

    chain_id = w3.eth.chain_id
    print(f"[+] Connected to Base (Chain ID: {chain_id})")

    account = w3.eth.account.from_key(private_key)
    deployer_address = account.address
    print(f"[+] Deployer Address: {deployer_address}")

    balance_wei = w3.eth.get_balance(deployer_address)
    balance_eth = w3.from_wei(balance_wei, "ether")
    print(f"[+] Live Balance: {balance_eth:.6f} ETH")

    if balance_eth < 0.0002:
        print("❌ Insufficient gas for deployment. Need at least 0.0002 ETH.")
        return

    abi, bytecode = compile_oracle_contract()
    print(f"[+] Contract compiled successfully ({len(bytecode)//2} bytes)")

    # Treasury & Operator addresses
    treasury_address = deployer_address
    operator_address = deployer_address
    initial_query_fee = w3.to_wei(0.0001, "ether") # ~ $0.25 USD

    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    nonce = w3.eth.get_transaction_count(deployer_address, "pending")
    gas_price = w3.eth.gas_price

    print("[*] Estimating gas and constructing deployment transaction...")
    construct_txn = contract.constructor(
        treasury_address,
        operator_address,
        initial_query_fee
    ).build_transaction({
        "from": deployer_address,
        "nonce": nonce,
        "gasPrice": int(gas_price * 1.2),
        "chainId": chain_id
    })

    gas_estimate = w3.eth.estimate_gas(construct_txn)
    construct_txn["gas"] = int(gas_estimate * 1.2)

    est_cost_eth = w3.from_wei(construct_txn["gas"] * construct_txn["gasPrice"], "ether")
    print(f"[*] Estimated Gas Cost: {est_cost_eth:.6f} ETH (~$0.02 USD)")

    print("[*] Signing and broadcasting transaction to Base Mainnet...")
    signed_txn = w3.eth.account.sign_transaction(construct_txn, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"[+] Transaction Broadcasted! TX Hash: {tx_hash.hex()}")
    print(f"👉 BaseScan TX: https://basescan.org/tx/{tx_hash.hex()}")

    print("[*] Waiting for transaction confirmation on Base L2...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    
    if receipt.status == 1:
        contract_address = receipt.contractAddress
        print("==========================================================")
        print("🎉 CONTRACT DEPLOYED SUCCESSFULLY ON BASE MAINNET!")
        print(f"📍 Oracle Address: {contract_address}")
        print(f"👉 BaseScan Contract: https://basescan.org/address/{contract_address}")
        print("==========================================================")

        # Save deployment info
        deployments_dir = Path("deployments")
        deployments_dir.mkdir(exist_ok=True)
        dep_data = {
            "network": "BASE_MAINNET",
            "chain_id": chain_id,
            "contract_address": contract_address,
            "deployer": deployer_address,
            "treasury": treasury_address,
            "operator": operator_address,
            "query_fee_eth": "0.0001",
            "tx_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber
        }
        with open(deployments_dir / "base_mainnet_oracle.json", "w", encoding="utf-8") as f:
            json.dump(dep_data, f, indent=2)
        print(f"[+] Saved deployment metadata to deployments/base_mainnet_oracle.json")
    else:
        print("❌ Deployment transaction reverted on-chain.")


if __name__ == "__main__":
    main()
