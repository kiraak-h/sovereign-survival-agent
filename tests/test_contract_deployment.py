# sovereign-survival-agent/tests/test_contract_deployment.py
"""
Test Suite for On-Chain AgentPolicyGuard Smart Contract Deployment & Verification.
"""
import pytest
import json
from pathlib import Path
from scripts.deploy_policy_guard import compile_agent_policy_guard
from scripts.broadcast_live_tx import get_connected_w3, BASE_SEPOLIA_CHAIN_ID


def test_compile_agent_policy_guard():
    abi, bytecode = compile_agent_policy_guard()
    assert len(abi) > 10
    assert len(bytecode) > 1000
    # Verify key functions exist in ABI
    func_names = [f.get("name") for f in abi if f.get("type") == "function"]
    assert "owner" in func_names
    assert "agentSessionKey" in func_names
    assert "dailySpendLimit" in func_names
    assert "executeAsAgent" in func_names



def test_query_deployed_onchain_policy_guard():
    manifest_path = Path("deployments/base_sepolia.json")
    assert manifest_path.exists()
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    contract_addr = data.get("contract_address")
    assert contract_addr.startswith("0x")
    assert data.get("status") == "DEPLOYED_LIVE_ON_CHAIN"

    # Query live on-chain contract state via Web3
    w3, rpc = get_connected_w3()
    abi_path = Path("contracts/AgentPolicyGuard.abi.json")
    with open(abi_path, "r", encoding="utf-8") as f:
        abi = json.load(f)

    guard = w3.eth.contract(address=contract_addr, abi=abi)
    owner = guard.functions.owner().call()
    session_key = guard.functions.agentSessionKey().call()
    daily_limit = guard.functions.dailySpendLimit().call()

    assert owner == data.get("owner_address")
    assert session_key == data.get("session_key_address")
    assert daily_limit > 0
