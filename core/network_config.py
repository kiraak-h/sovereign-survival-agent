# sovereign-survival-agent/core/network_config.py
"""
Multi-Network Web3 & Base L2 Configuration:
Seamlessly switches between Base Sepolia (Testnet) and Base Mainnet (Production),
managing RPCs, contract addresses, EAS registries, and official USDC contracts.
"""
from __future__ import annotations
import os
from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel


class NetworkMode(str, Enum):
    BASE_SEPOLIA = "BASE_SEPOLIA"
    BASE_MAINNET = "BASE_MAINNET"


class NetworkSpecs(BaseModel):
    name: str
    chain_id: int
    rpc_urls: List[str]
    explorer_url: str
    usdc_address: str
    usdc_decimals: int
    eas_contract: str
    schema_registry: str
    is_production: bool


NETWORKS: Dict[NetworkMode, NetworkSpecs] = {
    NetworkMode.BASE_SEPOLIA: NetworkSpecs(
        name="Base Sepolia Testnet",
        chain_id=84532,
        rpc_urls=[
            "https://sepolia.base.org",
            "https://base-sepolia-rpc.publicnode.com",
            "https://base-sepolia.blockpi.network/v1/rpc/public"
        ],
        explorer_url="https://sepolia.basescan.org",
        usdc_address="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        usdc_decimals=6,
        eas_contract="0x4200000000000000000000000000000000000021",
        schema_registry="0x4200000000000000000000000000000000000020",
        is_production=False
    ),
    NetworkMode.BASE_MAINNET: NetworkSpecs(
        name="Base Mainnet (Production)",
        chain_id=8453,
        rpc_urls=[
            "https://mainnet.base.org",
            "https://base-rpc.publicnode.com",
            "https://base.blockpi.network/v1/rpc/public"
        ],
        explorer_url="https://basescan.org",
        usdc_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # Official Base Mainnet Native USDC
        usdc_decimals=6,
        eas_contract="0x4200000000000000000000000000000000000021",
        schema_registry="0x4200000000000000000000000000000000000020",
        is_production=True
    )
}


def get_active_network() -> NetworkSpecs:
    """Returns currently active network based on NETWORK_MODE env variable."""
    mode_str = os.getenv("NETWORK_MODE", "BASE_MAINNET").upper()
    if mode_str in ("BASE_SEPOLIA", "SEPOLIA", "TESTNET"):
        return NETWORKS[NetworkMode.BASE_SEPOLIA]
    return NETWORKS[NetworkMode.BASE_MAINNET]


def get_live_onchain_balances(wallet_address: str) -> Dict[str, Any]:
    """Queries real live on-chain ETH and USDC balances directly from active Base network RPC."""
    try:
        from web3 import Web3
        net = get_active_network()
        for rpc in net.rpc_urls:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 5.0}))
                if not w3.is_connected():
                    continue
                chk_addr = Web3.to_checksum_address(wallet_address)
                
                # 1. Real on-chain ETH
                raw_wei = w3.eth.get_balance(chk_addr)
                eth_bal = float(w3.from_wei(raw_wei, "ether"))
                
                # 2. Real on-chain USDC
                usdc_abi = [{"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}]
                usdc_contract = w3.eth.contract(address=Web3.to_checksum_address(net.usdc_address), abi=usdc_abi)
                raw_usdc = usdc_contract.functions.balanceOf(chk_addr).call()
                usdc_bal = float(raw_usdc / (10 ** net.usdc_decimals))
                
                return {"eth": eth_bal, "usdc": usdc_bal, "network": net.name, "success": True}
            except Exception:
                continue
    except Exception:
        pass
    return {"eth": 0.0, "usdc": 0.0, "network": "Base Mainnet", "success": False}


