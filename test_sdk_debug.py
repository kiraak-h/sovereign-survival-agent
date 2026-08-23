import time
from sdk.python.sovereign_oracle.client import SovereignOracleClient
from eth_account import Account

bot_account = Account.create()
client = SovereignOracleClient(agent_id="test_bot_1", private_key=bot_account.key.hex())
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
    result = client.audit_contract(code=sample_contract)
    print("RAW RESULT:", result)
except Exception as e:
    print(f"Test Failed: {e}")
