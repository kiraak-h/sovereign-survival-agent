# sovereign-survival-agent/tests/test_contract_deployment.py
"""
Test Suite for On-Chain AgentPolicyGuard Smart Contract Deployment & Verification.
"""
import pytest
import json
from pathlib import Path
from web3 import Web3
from scripts.deploy_policy_guard import compile_agent_policy_guard
from core.network_config import NETWORKS, NetworkMode


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


def test_query_deployed_sepolia_policy_guard():
    manifest_path = Path("deployments/base_sepolia.json")
    assert manifest_path.exists()
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    contract_addr = data.get("contract_address")
    assert contract_addr.startswith("0x")
    assert data.get("status") == "DEPLOYED_LIVE_ON_CHAIN"

    # Query live on-chain contract state via Web3 on Base Sepolia
    sepolia_rpc = NETWORKS[NetworkMode.BASE_SEPOLIA].rpc_urls[0]
    w3 = Web3(Web3.HTTPProvider(sepolia_rpc, request_kwargs={"timeout": 6}))
    if w3.is_connected():
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


def test_query_deployed_mainnet_policy_guard():
    manifest_path = Path("deployments/base_mainnet.json")
    if not manifest_path.exists():
        pytest.skip("Base mainnet deployment manifest not found")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    contract_addr = data.get("contract_address")
    assert contract_addr.startswith("0x")

    # Query live on-chain contract state via Web3 on Base Mainnet
    mainnet_rpc = NETWORKS[NetworkMode.BASE_MAINNET].rpc_urls[0]
    w3 = Web3(Web3.HTTPProvider(mainnet_rpc, request_kwargs={"timeout": 6}))
    if w3.is_connected():
        abi_path = Path("contracts/AgentPolicyGuard.abi.json")
        with open(abi_path, "r", encoding="utf-8") as f:
            abi = json.load(f)

        guard = w3.eth.contract(address=contract_addr, abi=abi)
        owner = guard.functions.owner().call()
        session_key = guard.functions.agentSessionKey().call()
        daily_limit = guard.functions.dailySpendLimit().call()

        assert owner == data.get("master_address")
        assert session_key == data.get("session_key_address")
        assert daily_limit > 0
