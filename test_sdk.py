import time
from sdk.python.sovereign_oracle.client import SovereignOracleClient
from eth_account import Account

# Generate a random private key for the test bot
bot_account = Account.create()

print(f"Test Bot Address: {bot_account.address}")

client = SovereignOracleClient(
    agent_id="test_bot_1",
    private_key=bot_account.key.hex()
)

# Point to local server for testing
client.BASE_URL = "http://localhost:10000/v1"

sample_contract = """
pragma solidity ^0.8.20;
contract Honeypot {
    address public owner;
    constructor() { owner = msg.sender; }
    function withdraw() public {
        require(msg.sender == owner);
        payable(msg.sender).transfer(address(this).balance);
    }
}
"""

try:
    print("Sending A2A audit request with EIP-2612 permit...")
    result = client.audit_contract(code=sample_contract)
    print(f"Success! Security Score: {result['security_score']}/100")
    print(f"Findings: {result['findings']}")
except Exception as e:
    print(f"Test Failed: {e}")
