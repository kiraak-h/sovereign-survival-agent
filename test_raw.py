import time
import requests
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

permit = client._generate_usdc_permit(nonce=0, deadline=int(time.time()) + 3600)
payload = {
    "client_agent_id": client.agent_id,
    "contract_name": "TargetToken.sol",
    "code": sample_contract,
    "payment_permit": permit,
    "max_budget_usdc": 0.25
}
res = requests.post(f"{client.BASE_URL}/a2a/audit", json=payload)
print("STATUS:", res.status_code)
print("BODY:", res.text)
