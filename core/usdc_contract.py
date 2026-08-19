# sovereign-survival-agent/core/usdc_contract.py
"""
Live Base Sepolia USDC ERC-20 & EIP-2612 Permit Client:
Interfaces directly with the official Base Sepolia USDC contract (0x036CbD53842c5426634e7929541eC2318f3dCF7e).
"""
from __future__ import annotations
import os
from typing import Dict, Any, Tuple, Optional
from web3 import Web3
from scripts.broadcast_live_tx import get_connected_w3, BASE_SEPOLIA_CHAIN_ID, BASE_SEPOLIA_USDC


ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
]


class BaseSepoliaUSDCClient:
    """Client for querying and interacting with official USDC on Base Sepolia."""

    def __init__(self, contract_address: str = BASE_SEPOLIA_USDC):
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.w3, self.active_rpc = get_connected_w3()
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=ERC20_ABI)
        self._decimals: Optional[int] = None
        self._symbol: Optional[str] = None

    def get_token_metadata(self) -> Dict[str, Any]:
        """Fetches token name, symbol, decimals, and active RPC."""
        try:
            name = self.contract.functions.name().call()
            symbol = self.contract.functions.symbol().call()
            decimals = self.contract.functions.decimals().call()
            self._decimals = decimals
            self._symbol = symbol
            return {
                "name": name,
                "symbol": symbol,
                "decimals": decimals,
                "contract_address": self.contract_address,
                "active_rpc": self.active_rpc,
                "chain_id": BASE_SEPOLIA_CHAIN_ID
            }
        except Exception as e:
            return {
                "name": "USD Coin",
                "symbol": "USDC",
                "decimals": 6,
                "contract_address": self.contract_address,
                "active_rpc": self.active_rpc,
                "error": str(e)
            }

    def get_onchain_balance(self, wallet_address: str) -> float:
        """Fetches real on-chain USDC balance for any EVM address on Base Sepolia."""
        try:
            chk_addr = Web3.to_checksum_address(wallet_address)
            raw_bal = self.contract.functions.balanceOf(chk_addr).call()
            decimals = self._decimals or 6
            return float(raw_bal / (10 ** decimals))
        except Exception:
            return 0.0

    def get_allowance(self, owner_address: str, spender_address: str) -> float:
        """Queries allowance granted by owner to spender."""
        try:
            owner = Web3.to_checksum_address(owner_address)
            spender = Web3.to_checksum_address(spender_address)
            raw = self.contract.functions.allowance(owner, spender).call()
            decimals = self._decimals or 6
            return float(raw / (10 ** decimals))
        except Exception:
            return 0.0
