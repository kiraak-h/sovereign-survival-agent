# sovereign-survival-agent/tests/test_real_integrations.py
"""
Automated Test Suite for Real Static Analysis (solc 0.8.20) and Base Sepolia USDC ERC-20 Client.
"""
import pytest
from core.static_analyzer import RealSolidityStaticAnalyzer
from core.usdc_contract import BaseSepoliaUSDCClient


def test_real_solidity_static_analyzer_detects_reentrancy():
    analyzer = RealSolidityStaticAnalyzer()
    vuln_code = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerableVault {
    mapping(address => uint256) public balances;

    function withdraw() external {
        uint256 bal = balances[msg.sender];
        (bool s, ) = msg.sender.call{value: bal}("");
        require(s);
        balances[msg.sender] = 0;
    }
}
"""
    report = analyzer.analyze(vuln_code)
    assert report.status == "VULNERABLE"
    assert report.security_score < 70
    finding_ids = [f.id for f in report.findings]
    assert "SWC-107" in finding_ids


def test_real_solidity_static_analyzer_verifies_secure_contract():
    analyzer = RealSolidityStaticAnalyzer()
    secure_code = """// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

contract SecureVault {
    mapping(address => uint256) public balances;

    function withdraw() external {
        uint256 bal = balances[msg.sender];
        balances[msg.sender] = 0;
        (bool s, ) = msg.sender.call{value: bal}("");
        require(s, "Transfer failed");
    }
}
"""
    report = analyzer.analyze(secure_code)
    assert report.compiled_successfully is True
    assert report.security_score >= 90
    assert report.status == "SECURE"


def test_base_sepolia_usdc_client_metadata():
    client = BaseSepoliaUSDCClient()
    meta = client.get_token_metadata()
    assert meta["symbol"] == "USDC"
    assert meta["decimals"] == 6
    assert meta["contract_address"].startswith("0x")


def test_base_sepolia_usdc_client_queries_balance():
    client = BaseSepoliaUSDCClient()
    agent_addr = "0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA"
    balance = client.get_onchain_balance(agent_addr)
    assert isinstance(balance, float)
    assert balance >= 0.0
