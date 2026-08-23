# Sovereign Oracle (M2M Python SDK)

The official Python SDK for autonomous Web3 AI agents (e.g., AutoGPT, LangChain, ElizaOS) to programmatically audit smart contracts on-the-fly.

## The Problem
Your trading bot finds a new token on Base. Before it buys, it needs to know if the contract is a honeypot or contains a backdoor. 

## The Solution
The Sovereign Agent operates an **A2A (Agent-to-Agent)** Security Oracle.
Using this SDK, your bot can securely sign a $0.25 USDC micropayment (via EIP-2612) and get an instant, deterministic security score back.

### Security Guarantee
Your bot private key NEVER leaves your local machine. It is only used to cryptographically sign the USDC permit locally.

## Usage

```python
from sovereign_oracle.client import SovereignOracleClient

# 1. Initialize with your bots private key (Kept strictly local)
client = SovereignOracleClient(
    agent_id="my_trading_bot_v1",
    private_key="0xYOUR_BOTS_PRIVATE_KEY"
)

# 2. Audit a contract dynamically before buying
code = "contract Honeypot { ... }"

try:
    result = client.audit_contract(
        code=code, 
        contract_name="TargetToken.sol",
        nonce=0 # Get your wallets current USDC nonce from the RPC
    )
    
    print(f"Security Score: {result[\"security_score\"]}/100")
    print(f"Is Safe to Trade? {result[\"verified\"]}")
    
except Exception as e:
    print(f"Audit failed or payment rejected: {e}")
```
