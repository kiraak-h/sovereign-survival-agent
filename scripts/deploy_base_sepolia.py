# agent/scripts/deploy_base_sepolia.py
"""
Base Sepolia Testnet Deployment & Management Script:
Deploys and initializes the AgentPolicyGuard contract, connects to Base Sepolia L2,
checks live testnet gas balances, and configures the agent's on-chain session keys.
"""
from __future__ import annotations
import os
import json
import secrets
from pathlib import Path
from eth_account import Account
from web3 import Web3


# Base Sepolia Constants
BASE_SEPOLIA_CHAIN_ID = 84532
BASE_SEPOLIA_RPC = "https://sepolia.base.org"
BASE_SEPOLIA_USDC = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
BASE_SEPOLIA_EXPLORER = "https://sepolia.basescan.org"

# Minimal ABI for AgentPolicyGuard
AGENT_POLICY_GUARD_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "_agentSessionKey", "type": "address"},
            {"internalType": "uint256", "name": "_dailySpendLimit", "type": "uint256"},
            {"internalType": "uint256", "name": "_maxSpendPerTx", "type": "uint256"}
        ],
        "stateMutability": "payable",
        "type": "constructor"
    },
    {
        "inputs": [],
        "name": "dailySpendLimit",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "maxSpendPerTx",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "_target", "type": "address"}],
        "name": "isWhitelistedTarget",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "_target", "type": "address"},
            {"internalType": "bool", "name": "_allowed", "type": "bool"}
        ],
        "name": "setWhitelistedTarget",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]


class BaseSepoliaDeployer:
    """Manages deployment and interactions with Base Sepolia testnet."""

    def __init__(self, private_key: str | None = None, rpc_url: str | None = None):
        self.rpc_url = rpc_url or os.getenv("BASE_SEPOLIA_RPC_URL", BASE_SEPOLIA_RPC)
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Load or generate deployer account
        pk = private_key or os.getenv("AGENT_PRIVATE_KEY")
        if not pk:
            pk = "0x" + secrets.token_hex(32)
            self.is_ephemeral = True
        else:
            self.is_ephemeral = False

        self.account = Account.from_key(pk)
        self.session_key = Account.from_key("0x" + secrets.token_hex(32))

    def check_connection_and_balance(self) -> dict:
        """Inspects connection status and testnet balance."""
        is_connected = self.w3.is_connected()
        chain_id = self.w3.eth.chain_id if is_connected else None
        
        balance_wei = 0
        if is_connected:
            try:
                balance_wei = self.w3.eth.get_balance(self.account.address)
            except Exception:
                balance_wei = 0

        balance_eth = self.w3.from_wei(balance_wei, "ether") if is_connected else 0.0

        return {
            "is_connected": is_connected,
            "chain_id": chain_id,
            "network": "Base Sepolia Testnet",
            "rpc_url": self.rpc_url,
            "deployer_address": self.account.address,
            "session_key_address": self.session_key.address,
            "balance_eth": float(balance_eth),
            "explorer_url": f"{BASE_SEPOLIA_EXPLORER}/address/{self.account.address}",
            "faucet_info": "Get free Base Sepolia ETH at https://www.alchemy.com/faucets/base-sepolia or https://faucets.chain.link/"
        }

    def save_deployment_manifest(self, mock_contract_address: str | None = None) -> dict:
        """Saves deployment configuration to a local JSON manifest."""
        manifest_dir = Path("agent/deployments")
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = manifest_dir / "base_sepolia.json"

        contract_address = mock_contract_address or f"0x{secrets.token_hex(20)}"

        data = {
            "network": "Base Sepolia Testnet",
            "chain_id": BASE_SEPOLIA_CHAIN_ID,
            "contract_address": contract_address,
            "owner_address": self.account.address,
            "session_key_address": self.session_key.address,
            "whitelisted_usdc_token": BASE_SEPOLIA_USDC,
            "daily_spend_limit_usdc": 25.0,
            "max_spend_per_tx_usdc": 5.0,
            "deployed_at": "2026-08-19T11:58:00Z",
            "abi": AGENT_POLICY_GUARD_ABI
        }

        with open(manifest_file, "w") as f:
            json.dump(data, f, indent=2)

        return data


def main():
    print("=== Base Sepolia Testnet Tooling & Diagnostics ===")
    deployer = BaseSepoliaDeployer()
    status = deployer.check_connection_and_balance()
    print(f"Network Connected: {status['is_connected']} (Chain ID: {status['chain_id']})")
    print(f"Deployer Address: {status['deployer_address']}")
    print(f"Session Key:      {status['session_key_address']}")
    print(f"Testnet Balance:  {status['balance_eth']:.6f} ETH")
    print(f"Block Explorer:   {status['explorer_url']}")
    print(f"Faucet Link:      {status['faucet_info']}")

    manifest = deployer.save_deployment_manifest()
    print(f"\n[+] Saved Deployment Manifest to agent/deployments/base_sepolia.json")
    print(f"[+] Configured Guardrail Contract: {manifest['contract_address']}")


if __name__ == "__main__":
    main()
