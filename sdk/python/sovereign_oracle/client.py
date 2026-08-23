import time
import requests
from typing import Dict, Any, Optional
from eth_account.messages import encode_typed_data
from eth_account import Account

class SovereignOracleClient:
    """
    Machine-to-Machine (M2M) SDK for autonomous Web3 agents.
    Allows trading bots to dynamically audit smart contracts by paying $0.25 USDC
    per scan using EIP-2612 signatures natively on Base Mainnet.
    """
    
    BASE_URL = "https://sovereign-survival-agent.onrender.com/v1"
    USDC_BASE_MAINNET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    AGENT_TREASURY = "0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA"
    FEE_USDC = 0.25
    
    def __init__(self, agent_id: str, private_key: str):
        """
        Initializes the Oracle Client.
        The private key is kept STRICTLY LOCAL to sign EIP-2612 permits. 
        It is NEVER transmitted over the network.
        """
        self.agent_id = agent_id
        self.account = Account.from_key(private_key)
        
    def _generate_usdc_permit(self, nonce: int, deadline: int) -> Dict[str, Any]:
        """Generates an EIP-2612 USDC permit signature locally."""
        value = int(self.FEE_USDC * 1e6) # 6 decimals for USDC
        
        # Base Mainnet USDC EIP-712 Domain
        domain = {
            "name": "USD Coin",
            "version": "2",
            "chainId": 8453,
            "verifyingContract": self.USDC_BASE_MAINNET
        }
        
        # EIP-2612 Permit Types
        types = {
            "Permit": [
                {"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "deadline", "type": "uint256"}
            ]
        }
        
        message = {
            "owner": self.account.address,
            "spender": self.AGENT_TREASURY,
            "value": value,
            "nonce": nonce,
            "deadline": deadline
        }
        
        structured_data = {
            "types": types,
            "primaryType": "Permit",
            "domain": domain,
            "message": message
        }
        
        signable_message = encode_typed_data(full_message=structured_data)
        signed_message = self.account.sign_message(signable_message)
        
        return {
            "payer_address": self.account.address,
            "token_address": self.USDC_BASE_MAINNET,
            "amount_usdc": self.FEE_USDC,
            "nonce": nonce,
            "deadline": deadline,
            "signature": signed_message.signature.hex()
        }
        
    def audit_contract(self, code: str, contract_name: str = "Unknown.sol", nonce: int = 0) -> Dict[str, Any]:
        """
        Audits a smart contract by signing a $0.25 USDC micropayment and calling the A2A API.
        Requires the current USDC nonce of the agent's wallet to prevent replay failures.
        """
        deadline = int(time.time()) + 3600 # 1 hour validity
        permit = self._generate_usdc_permit(nonce=nonce, deadline=deadline)
        
        payload = {
            "client_agent_id": self.agent_id,
            "contract_name": contract_name,
            "code": code,
            "payment_permit": permit,
            "max_budget_usdc": self.FEE_USDC
        }
        
        response = requests.post(f"{self.BASE_URL}/a2a/audit", json=payload)
        
        if response.status_code == 402:
            raise Exception(f"Payment Required/Failed: {response.json().get('error')}")
        elif response.status_code != 200:
            raise Exception(f"Oracle Error {response.status_code}: {response.text}")
            
        return response.json()
