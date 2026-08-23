# sovereign-survival-agent/tests/test_institutional_engines.py
"""
Test Suite for 3 Institutional Sovereign Earning Engines:
- GitHub CI/CD Security Action
- Agent-to-Agent (A2A) HTTP-402 Verification Gateway
- On-Chain Base Security Oracle Contract
"""
import pytest
from pathlib import Path
from channels.a2a_gateway import A2AGateway, A2AAuditRequest
from channels.automated_contract_auditor import AutomatedContractAuditor
from core.metabolism import MetabolismManager
from core.wallet import SovereignWallet
from core.models import AgentState, PaymentPermit
from action.ci_runner import format_pr_comment, find_solidity_files
from scripts.deploy_oracle import compile_oracle_contract


def test_ci_runner_formats_pr_comment():
    sample_results = [
        {
            "contract_name": "Vault.sol",
            "security_score": 55,
            "status": "VULNERABLE",
            "findings_count": 1,
            "findings": [
                {
                    "severity": "HIGH",
                    "title": "Reentrancy Vulnerability",
                    "line": 15,
                    "description": "State modification occurs after external ether transfer.",
                    "recommendation": "Apply nonReentrant modifier."
                }
            ],
            "eas_attestation_url": "https://base-sepolia.easscan.org/attestation/view/0x1234"
        },
        {
            "contract_name": "Token.sol",
            "security_score": 100,
            "status": "SECURE",
            "findings_count": 0,
            "findings": [],
            "eas_attestation_url": "https://base-sepolia.easscan.org/attestation/view/0x5678"
        }
    ]

    comment = format_pr_comment(sample_results, overall_score=77, min_score=55)
    assert "Sovereign AI Smart Contract Security Audit" in comment
    assert "Vault.sol" in comment
    assert "Token.sol" in comment
    assert "Reentrancy Vulnerability" in comment
    assert "EAS Proof" in comment


def test_a2a_gateway_processes_valid_request(tmp_path):
    state = AgentState(
        agent_address="0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA",
        session_key_address="0x97F88CA501AF4A75C9F8fd8C56d230a43e407134",
        treasury_usdc=10.0
    )
    metabolism = MetabolismManager(state)
    wallet = SovereignWallet(state)
    auditor = AutomatedContractAuditor(reports_dir=str(tmp_path))
    gateway = A2AGateway(auditor=auditor, metabolism=metabolism, wallet=wallet)

    req = A2AAuditRequest(
        client_agent_id="Agent_ElizaOS_402",
        contract_name="RewardStaking.sol",
        code="""
        pragma solidity ^0.8.20;
        contract RewardStaking {
            mapping(address => uint256) public stakes;
            function stake() external payable {
                stakes[msg.sender] += msg.value;
            }
        }
        """,
        max_budget_usdc=0.25
    )

    success, data, status_code = gateway.process_a2a_request(req)
    assert success is True
    assert status_code == 200
    assert data["verified"] is True
    assert data["security_score"] >= 80
    assert data["fee_charged_usdc"] == 0.25
    assert metabolism.state.treasury_usdc == 10.25


def test_a2a_gateway_rejects_counterfeit_permit(tmp_path):
    state = AgentState(
        agent_address="0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA",
        session_key_address="0x97F88CA501AF4A75C9F8fd8C56d230a43e407134"
    )
    metabolism = MetabolismManager(state)
    wallet = SovereignWallet(state)
    auditor = AutomatedContractAuditor(reports_dir=str(tmp_path))
    gateway = A2AGateway(auditor=auditor, metabolism=metabolism, wallet=wallet)

    fake_permit = PaymentPermit(
        payer_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        token_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        amount_usdc=0.25,
        nonce=1,
        deadline=1893456000,
        signature="0x" + "0" * 130  # Invalid signature
    )

    req = A2AAuditRequest(
        client_agent_id="Rogue_Agent",
        contract_name="Contract.sol",
        code="contract Test {}",
        payment_permit=fake_permit
    )

    success, data, status_code = gateway.process_a2a_request(req)
    assert success is False
    assert status_code == 402
    assert "Invalid or counterfeit permit" in data["error"]


def test_compile_agent_security_oracle_solidity():
    abi, bytecode = compile_oracle_contract()
    assert len(abi) >= 15
    assert len(bytecode) > 1000
    method_names = [item.get("name") for item in abi if item.get("type") == "function"]
    assert "recordAudit" in method_names
    assert "queryContractSecurity" in method_names
    assert "hasAuditRecord" in method_names
