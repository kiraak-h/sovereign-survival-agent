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
    mode_str = os.getenv("NETWORK_MODE", "BASE_SEPOLIA").upper()
    if mode_str == "BASE_MAINNET" or mode_str == "MAINNET":
        return NETWORKS[NetworkMode.BASE_MAINNET]
    return NETWORKS[NetworkMode.BASE_SEPOLIA]
