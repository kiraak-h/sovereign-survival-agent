# sovereign-survival-agent/tests/test_automated_auditor.py
"""
Test Suite for Automated 24/7 Smart Contract Security Auditor.
"""
import pytest
from pathlib import Path
from channels.automated_contract_auditor import AutomatedContractAuditor, ContractAuditResult
from core.static_analyzer import RealSolidityStaticAnalyzer
from core.eas_attestation import EASAttestationManager
from core.notifier import AgentNotifier


def test_automated_auditor_analyzes_vulnerable_contract(tmp_path):
    auditor = AutomatedContractAuditor(reports_dir=str(tmp_path))
    
    vulnerable_solidity = """
    pragma solidity ^0.8.20;

    contract PhishingAndReentrancyVault {
        address public owner;
        mapping(address => uint256) public balances;

        constructor() {
            owner = msg.sender;
        }

        function withdrawAll() public {
            // Vulnerability 1: tx.origin auth
            require(tx.origin == owner, "Not owner");

            // Vulnerability 2: reentrancy & unchecked call
            uint256 bal = balances[msg.sender];
            (bool s, ) = msg.sender.call{value: bal}("");
            balances[msg.sender] = 0;
        }
    }
    """

    res: ContractAuditResult = auditor.audit_solidity_code(
        source_code=vulnerable_solidity,
        contract_name="PhishingVault.sol",
        target_ref="0x_sample_vulnerable",
        source_channel="Test"
    )

    assert res.status == "VULNERABLE"
    assert res.security_score < 70
    assert res.findings_count >= 2
    assert any("tx.origin" in f["title"] for f in res.findings)
    assert Path(res.report_file_path).exists()


def test_automated_auditor_analyzes_secure_contract(tmp_path):
    auditor = AutomatedContractAuditor(reports_dir=str(tmp_path))
    
    secure_solidity = """
    pragma solidity ^0.8.20;

    contract SecureTreasury {
        address public immutable owner;
        mapping(address => uint256) public balances;

        constructor() {
            owner = msg.sender;
        }

        function withdraw() public {
            require(msg.sender == owner, "Only owner");
            uint256 bal = balances[msg.sender];
            require(bal > 0, "No balance");
            
            // Checks-effects-interactions
            balances[msg.sender] = 0;
            (bool s, ) = msg.sender.call{value: bal}("");
            require(s, "Transfer failed");
        }
    }
    """

    res: ContractAuditResult = auditor.audit_solidity_code(
        source_code=secure_solidity,
        contract_name="SecureTreasury.sol",
        target_ref="0x_sample_secure",
        source_channel="Test"
    )

    assert res.status == "SECURE"
    assert res.security_score >= 80
    assert Path(res.report_file_path).exists()


def test_automated_auditor_json_bundle_extractor(tmp_path):
    auditor = AutomatedContractAuditor(reports_dir=str(tmp_path))
    bundle = '{"sources": {"Vault.sol": {"content": "contract Vault {}"}}}'
    extracted = auditor._extract_source_from_json_bundle(bundle)
    assert "contract Vault {}" in extracted
